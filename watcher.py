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

class WatchDir(object):
    SUPPORTED_EXTS = ['mp3', 'json']

    def __init__(self, watch_dir, done_dir, username, base_url, lcd):
        self.watch_dir = watch_dir
        self.done_dir = done_dir
        self.username = username
        self.base_url = base_url
        self.lcd = lcd

        self._mp3_worker = ThreadPoolExecutor(max_workers=2)
        self._json_worker = ThreadPoolExecutor(max_workers=1)
        self._current_work = {}

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
                finally:
                    del self._current_work[filepath]
                    
    def enqueue_files(self):
        for f in os.listdir(self.watch_dir):
            try:
                self.enqueue_file(f)
            except Exception as e:
                logging.exception('error uploading session')


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

    def wait_for_wifi(self):
        while not is_connected():
            self.lcd.write('Connecting to {} '.format(self.wifi_name), 0)
            time.sleep(1)

        self.lcd.write('Connected {} ({}) '.format(self.wifi_name, get_local_ip()), 0)
        self.lcd.write('User: {} '.format(self.username), 1)

    def watch(self):
        w = WatchDir(
            self.watch_dir,
            self.done_dir,
            self.username,
            self.base_url,
            self.lcd,
        )

        try:
            while True:
                #self.wait_for_wifi()
                w.enqueue_files()
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
