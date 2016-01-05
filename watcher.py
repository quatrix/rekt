#!/usr/bin/env python

import os
import subprocess
import requests
import time
import sys
import logging
import socket
import fcntl
import struct
import click

from Queue import Queue, Empty
from threading import Thread, Event
from utils import *
from lcd import FakeLCDManager, LCDManager

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class WatchDir(object):
	def __init__(self, watch_dir, done_dir, username, base_url, lcd):
		self.watch_dir = watch_dir
		self.done_dir = done_dir
		self.username = username
		self.base_url = base_url
		self.lcd = lcd

	def handle_mp3(self, session_id, filepath):
		url = '{}/upload/{}/{}'.format(self.base_url, self.username, session_id)

		r = requests.get(url)

		if r.status_code != 200:
			raise RuntimeError('({}): {}'.format(r.status_code, r.text))
			
		offset = int(r.text)

		r = requests.post(url, data=iterfile(filepath, offset))

		if r.status_code != 200:
			raise RuntimeError('({}): {}'.format(r.status_code, r.text))
		
	def handle_json(self, session_id, filepath):
		url = '{}/sessions/{}/{}'.format(self.base_url, self.username, session_id)

		r = requests.put(url, data=open(filepath).read())

		if r.status_code != 200:
			raise RuntimeError('({}): {}'.format(r.status_code, r.text))

	def process_file(self, filepath):
		session_id, ext = os.path.splitext(os.path.basename(filepath))
		getattr(self, 'handle_' + ext[1:])(session_id, filepath)
	
	def run_once(self):
		for f in os.listdir(self.watch_dir):
			filepath = os.path.join(self.watch_dir, f)
			donepath = os.path.join(self.done_dir, f)

			try:
				self.lcd.write(f, 0)
				self.process_file(filepath)
				os.rename(filepath, donepath)
				self.lcd.write("Upload: Done!", 1)
			except Exception as e:
				logging.exception('error uploading session')
				self.lcd.write('Error: {}'.format(e), 1)
				time.sleep(10)


def init_lcd(no_pi):
	if no_pi:
		lcd = FakeLCDManager()
	else:
		lcd = LCDManager()

	lcd.start()
	return lcd


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
			self.lcd.write('Connecting to {} '.format(wifi_name), 0)
			time.sleep(1)

		self.lcd.write('Connected {} ({}) '.format(self.wifi_name, get_local_ip()), 0)
		self.lcd.write('User: {} '.format(self.username), 1)

	def watch(self):
		while True:
			#self.wait_for_wifi()

			WatchDir(
				self.watch_dir,
				self.done_dir,
				self.username,
				self.base_url,
				self.lcd,
			).run_once()

			time.sleep(1)

	def __del__(self):
		self.lcd.stop()

@click.command()
@click.option('--work-dir', default='/rec', help='watch dir')
@click.option('--no-pi', is_flag=True, default=False, help='not on raspberry pi?')
@click.option('--base-url', default='http://edisdead.com:55666', help='rekt server url')
def main(work_dir, no_pi, base_url):
	Watcher(work_dir, no_pi, base_url).watch()

if __name__ == '__main__':
	main()
