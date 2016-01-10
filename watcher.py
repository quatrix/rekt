#!/usr/bin/env python

import os
import subprocess
import requests
import time
import sys
import logging
import click
import signal

from utils import *
from lcd import FakeLCDManager, LCDManager
from threading import Event
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


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

        if ext not in self.SUPPORTED_EXTS:
            return

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



def init_lcd(no_pi):
    if no_pi:
        lcd = FakeLCDManager()
    else:
        lcd = LCDManager()

    lcd.start()
    return lcd

def suicide():
    logging.info('commiting suicide, bye')
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)


class Watcher(object):
    def __init__(self, work_dir, no_pi, base_url):
        self.wifi_name = get_wifi_name(work_dir)
        self.username = get_username(work_dir)
        self.base_url = base_url

        self.watch_dir = os.path.join(work_dir, 'to_upload')
        self.done_dir = os.path.join(work_dir, 'done')

        self.lcd = init_lcd(no_pi)
        self.upload_tracker = UploadTracker()

    def wait_for_wifi(self):
        while not is_connected():
            self.lcd.write('Connecting to {} '.format(self.wifi_name), 0)
            time.sleep(1)

        self.lcd.write('WIFI: {} ({}) User: {} '.format(
            self.wifi_name,
            get_local_ip(),
            self.username
        ), 0)

    def update_lcd_with_upload_state(self):
        progress = self.upload_tracker.get_state()

        if progress:
            self.lcd.write(' '.join(progress) + ' ', 1)
        else:
            self.lcd.write('Hold to record', 1)

    def watch(self):
        w = WatchDir(
            self.watch_dir,
            self.done_dir,
            self.username,
            self.base_url,
            self.upload_tracker,
        )

        try:
            while True:
                self.wait_for_wifi()
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
@click.option('--work-dir', default='/rec', help='watch dir')
@click.option('--no-pi', is_flag=True, default=False, help='not on raspberry pi?')
@click.option('--base-url', default='http://edisdead.com:55666', help='rekt server url')
def main(work_dir, no_pi, base_url):
    Watcher(work_dir, no_pi, base_url).watch()

if __name__ == '__main__':
    main()
