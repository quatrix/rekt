#!/usr/bin/env python

import os
import subprocess
import requests
import time
import sys
import logging
import click
import signal
import json
import types

from utils import *
from lcd import LCDManager
from threading import Event
from concurrent.futures import ThreadPoolExecutor
from sh import pidof

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class DoneUploading(object):
    pass


class UploadError(object):
    def __init__(self):
        self.time = time.time()

    @property
    def expired(self):
        return time.time() - self.time > 5


class UploadTracker(object):
    def __init__(self):
        self._state = {}

    def set_done(self, key):
        self._state.pop(key)

    def set_error(self, key):
        self._state[key] = UploadError()

    def set_uploading(self, key):
        if key not in self._state:
            self._state[key] = True

    def get_state(self):
        res = []

        for k, v in self._state.iteritems():
            if isinstance(v, UploadError) and not v.expired:
                res.append('{}: Error'.format(k))
            else:
                res.append(('{}: Uploading'.format(k)))

        return res


class WatchDir(object):
    SUPPORTED_EXTS = ['mp3', 'json']

    def __init__(self, watch_dir, done_dir, username, base_url, state_manager):
        self.watch_dir = watch_dir
        self.done_dir = done_dir
        self.username = username
        self.base_url = base_url

        self._mp3_worker = ThreadPoolExecutor(max_workers=2)
        self._json_worker = ThreadPoolExecutor(max_workers=1)
        self._current_work = {}
        self.state_manager = state_manager

    def upload_json(self, filepath, session_id):
        logging.info('upload json %s', filepath)

        url = '{}/sessions/{}/{}'.format(self.base_url, self.username, session_id)
        logging.info('upload json url: %s', url)

        r = requests.put(url, data=open(filepath).read())

        if r.status_code != 200:
            raise RuntimeError('({}): {}'.format(r.status_code, r.text))

    def upload_mp3(self, filepath, session_id):
        logging.info('upload mp3 %s', filepath)

        url = '{}/upload/{}/{}'.format(self.base_url, self.username, session_id)
        logging.info('upload mp3 url: %s', url)

        r = requests.get(url)

        if r.status_code != 200:
            raise RuntimeError('({}): {}'.format(r.status_code, r.text))
            
        offset = int(r.text)
        logging.info('upload mp3 got offset: %d', offset)

        r = requests.post(url, data=iterfile(filepath, offset))

        if r.status_code != 200:
            raise RuntimeError('({}): {}'.format(r.status_code, r.text))

    def get_worker(self, ext):
        worker = getattr(self, '_{}_worker'.format(ext))
        task =  getattr(self, 'upload_{}'.format(ext))

        return worker, task

    def enqueue_file(self, f):
        session_id, ext = get_session_and_ext(f)

        logging.info('enqueue_file || session_id: "%s" ext: "%s"', session_id, ext)

        if ext not in self.SUPPORTED_EXTS:
            logging.info('ext "%s" not supported', ext)
            return

        logging.info('ext "%s" supported', ext)

        filepath = os.path.join(self.watch_dir, f)
        donepath = os.path.join(self.done_dir, f)

        worker, task = self.get_worker(ext)

        if filepath not in self._current_work:
            self._current_work[filepath] = worker.submit(task, filepath, session_id)
        else:
            if self._current_work[filepath].done():
                try:
                    self._current_work[filepath].result()
                    logging.info('done, renaming %s -> %s', filepath, donepath)
                    os.rename(filepath, donepath)
                    return DoneUploading
                finally:
                    self._current_work.pop(filepath)
                    
    def enqueue_files(self):
        for f in os.listdir(self.watch_dir):
            try:
                self.state_manager.set_uploading(f)

                if self.enqueue_file(f) == DoneUploading:
                    self.state_manager.set_done(f)

            except Exception as e:
                logging.exception('error uploading session')
                self.state_manager.set_error(f)



def suicide():
    logging.info('commiting suicide, bye')
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)

def lcd_parallel_driver():
    lcd_rs        = 26  # Note this might need to be changed to 21 for older revision Pi's.
    lcd_en        = 19
    lcd_d4        = 13
    lcd_d5        = 6
    lcd_d6        = 5
    lcd_d7        = 11
    lcd_backlight = 4

    lcd_columns = 16
    lcd_rows    = 2

    import Adafruit_CharLCD as LCD

    lcd = LCD.Adafruit_CharLCD(
        lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
        lcd_columns, lcd_rows, lcd_backlight
    )

    def write_line(self, text, line):
        self.set_cursor(0, line)

        for char in text:
            self.write8(ord(char), True)

    def clear_line(self, line):
        self.set_cursor(0, line)
        self.write_line(' '*lcd_columns, line)

    lcd.clear_line= types.MethodType(clear_line, lcd)
    lcd.write_line = types.MethodType(write_line, lcd)

    return lcd

def lcd_i2c_driver():
    import RPi_I2C_driver

    lcd = RPi_I2C_driver.lcd()

    def write_line(self, text, line):
        logging.info('writing to line %d: %s', line, text)
        self.lcd_display_string(text, line+1)

    def clear_line(self, line):
        self.lcd_display_string(' ' * 16, line+1)


    lcd.clear_line= types.MethodType(clear_line, lcd)
    lcd.write_line = types.MethodType(write_line, lcd)

    return lcd

def get_lcd_driver():
    if 'LCD_I2C' in os.environ:
        logging.info('lcd: using i2c driver')
        return lcd_i2c_driver()

    logging.info('lcd: using parallel driver')
    return lcd_parallel_driver()


class Watcher(object):
    def __init__(self, no_pi, base_url):
        self.base_url = base_url

        self.lcd = LCDManager(get_lcd_driver())
        self.lcd.start()
        self.upload_tracker = UploadTracker()

    def initialize(self):
        work_dir = find_work_dir()

        if work_dir is None:
            raise RuntimeError('Can\'t find mimosa.json')

        logging.info('work dir found: %s', work_dir)

        try:
            self.config_file = os.path.join(work_dir, 'mimosa.json')
            self.config = json.loads(open(self.config_file).read())
        except Exception as e:
            raise RuntimeError('mimosa.json seems invalid')

        self.watch_dir = os.path.join(work_dir, 'to_upload')
        self.done_dir = os.path.join(work_dir, 'done')
        mkdir_if_not_exists(self.watch_dir)
        mkdir_if_not_exists(self.done_dir)

        logging.info('waiting for network manager to start')
        self.wait_for_network_manager_to_start()

        if not self.connect_to_wifi():
            raise RuntimeError('Can\'t find WiFi')

        logging.info('getting configuration updates')
        self.get_updates()

        if hasattr(self, 'need_to_reconnect_to_wifi'):
            self.lcd.write('Config Updated', 0)
            self.lcd.write('reconnecting...', 1)
            time.sleep(1)

            if not self.connect_to_wifi():
                raise RuntimeError('Can\'t find WiFi')

    def get_updates(self):
        url = '{}/config/{}'.format(self.base_url, self.config['username'])
        logging.info('config url: %s', url)

        try:
            config = requests.get(url).json()

            if 'error' in config:
                logging.error('server returned error when asking for config: %s', config['error'])
                return

            if config != self.config:
                logging.info('configuration changed!')
                if config['wifi'] != self.config['wifi']:
                    logging.info('wifi changed!')
                    self.need_to_reconnect_to_wifi = True
                else:
                    logging.info('wifi didn\'t change')

                self.config = config
                open(self.config_file, 'w').write(json.dumps(config))
            else:
                logging.info('configuration didn\'t change')
        except Exception:
            logging.exception('get updates')
         

    def wait_for_network_manager_to_start(self):
        while True:
            try:
                if pidof('NetworkManager'):
                    return
            except Exception:
                pass

            time.sleep(1)

    def connect_to_wifi(self):
        wifi_ssid = self.config['wifi']['ssid']
        wifi_pass = self.config['wifi']['pass']
        username = self.config['username']
        attempts = 5

        connected_wifi = get_connected_wifi()

        if connected_wifi == wifi_ssid:
            logging.info('connected to the wifi specified in mimosa.json')
            return True

        if connected_wifi is None:
            logging.error('not connected')
        else:
            logging.error('connected to %s, this is not what is specified in mimosa.json', connected_wifi)

        for attempt in xrange(attempts):
            self.lcd.write('Connecting to', 0)
            self.lcd.write('{}... {}/{}'.format(wifi_ssid[0:9], attempt + 1, attempts), 1)

            try:
                connect_to_wifi(wifi_ssid, wifi_pass)
                connected_wifi = get_connected_wifi()

                if connected_wifi == wifi_ssid:
                    logging.info('connected to the wifi specified in mimosa.json')
                    return True
            except Exception:
                logging.exception('connect to wifi')

            time.sleep(1)

        logging.error('couldn\'t connect to wifi specified in mimosa.json, trying any wifi')

        for attempt in xrange(attempts):
            self.lcd.write('Trying other', 0)
            self.lcd.write('WiFis.. {}/{}'.format(attempt + 1, attempts), 1)
            connect_to_any_wifi()
            connected_wifi = get_connected_wifi()

            logging.info('connected wifi: "%s"', connected_wifi)

            if connected_wifi is not None:
                return True

            time.sleep(1)

        self.lcd.write('No WiFi found', 0)
        self.lcd.write('Retrying...', 1)

    def update_lcd_with_upload_state(self):
        progress = self.upload_tracker.get_state()

        if progress:
            self.lcd.write(' '.join(progress) + ' ', 1)
        else:
            self.lcd.write('', 1)

    def wait_for_sane_state(self):
        attempts = 0

        while True:
            try:
                self.lcd.write('Initializing...', 0)
                self.initialize()
                break
            except Exception as e:
                logging.exception('initialize')

                if attempts > 5:
                    self.lcd.write('Init failed:', 0)
                    self.lcd.write(e.message + ' ', 1)

                attempts += 1
                time.sleep(1)

    def wait_for_connectivity(self):
        while True:
            if is_connected():
                return

            self.lcd.write('No network', 1)
            time.sleep(1)
        
    def print_wifi_info(self):
        connected_wifi = get_connected_wifi()
        if connected_wifi:
            self.lcd.write('{} ({}) '.format(connected_wifi, get_local_ip()), 0)
        else:
            self.lcd.write('No Wifi', 0)

    def watch(self):
        w = WatchDir(
            self.watch_dir,
            self.done_dir,
            self.config['username'],
            self.base_url,
            self.upload_tracker,
        )

        try:
            while True:
                self.print_wifi_info()
                self.wait_for_connectivity()
                w.enqueue_files()
                self.update_lcd_with_upload_state()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info('shut down the devil sound')
            suicide()

    def __del__(self):
        if hasattr(self, 'lcd'):
            self.lcd.stop()

@click.command()
@click.option('--no-pi', is_flag=True, default=False, help='not on raspberry pi?')
@click.option('--base-url', default='http://mimosabox.com:55666', help='rekt server url')
def main(no_pi, base_url):
    w = Watcher(no_pi, base_url)
    w.wait_for_sane_state()
    w.watch()

if __name__ == '__main__':
    main()
