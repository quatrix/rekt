#!/usr/bin/env python

import os
import re
import subprocess
import requests
import time
import sys
import logging
import RPi_I2C_driver

from Queue import Queue, Empty
from threading import Thread


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

waiting_to_upload_dir = '/rec/to_upload/'
done_dir = '/rec/done'
username = open('/rec/config/username').read().strip()

class LCDManager(object):
	def __init__(self):
		self.q = Queue()
		self.lcd = LCD()

	def run(self):
		while True:
			try:
				command = self.q.get_nowait()
				msg, line = command
				self.lcd.set(msg, line)
			except Empty:
				pass

			self.lcd.update()
			time.sleep(0.7)


	def write(self, msg, line):
		self.q.put((msg ,line))

	def start(self):
		Thread(target=self.run, args=()).start()



def scrolling_text(text, chars):
	while True:
		if len(text) < chars:
			yield text

		yield text[:chars-1]
		text = text[1:] + text[0]



class LCD(object):
	def __init__(self, chars=16, lines=2):
		self.lcd = RPi_I2C_driver.lcd()
		self.chars = chars
		self.lines = [None for _ in xrange(lines)]
		self._lines_text = [None for _ in xrange(lines)]


	def set(self, text, line):
		if self._lines_text[line] == text:
			return

		self._lines_text[line] = text
		self.lines[line] = scrolling_text(text, self.chars)

	def clear_line(self, line):
		self.lcd.lcd_display_string(' '*self.chars, line+1)

	def write_to_lcd(self, text, line):
		self.lcd.lcd_display_string(text, line+1)

	def update(self):
		for line, generator in enumerate(self.lines):
			if generator is None:
				continue

			self.clear_line(line)
			self.write_to_lcd(next(generator), line)


class Task(object):
	def __init__(self, session_dir):
		logging.info('working on %s', session_dir)
		self.session_dir = session_dir
		self.session_file = os.path.join(session_dir, 'session.mp3')
		self.metadata_file = os.path.join(session_dir, 'metadata.json')

	def check_sanity(self):
		if not os.path.exists(self.session_file):
			raise RuntimeError('{} - session file missing'.format(self.session_file))

		if not os.path.exists(self.metadata_file):
			raise RuntimeError('{} - metadata file missing'.format(self.metadata_file))

	def handle(self):
		self.check_sanity()
		self.upload_session()
		self.move_to_done()

	def upload_session(self):
		url = 'http://edisdead.com:55666/upload/{}/'.format(username)

		multiple_files = [
			('files[session]', ('session.mp3', open(self.session_file, 'rb'), 'audio/mpeg')),
			('files[metadata]', ('metadata.json', open(self.metadata_file, 'rb'), 'application/json'))
		]

		r = requests.post(url, files=multiple_files)

		if r.status_code != 200:
			raise RuntimeError(r.status_code)

		logging.info('done uploading %s', self.session_dir)

	def move_to_done(self):
		os.rename(self.session_dir, os.path.join(done_dir, os.path.basename(self.session_dir)))
		

wifi_re = re.compile(r'\s+wpa-ssid \"(.+)\"')

def get_wifi_name():
	for l in open('/rec/config/wifi').readlines():
		r = wifi_re.search(l)

		if r:
			return r.group(1)



def network_works():
	try:
		return requests.get('http://edisdead.com').status_code == 200
	except Exception:
		return False

		
lcd = LCDManager()
lcd.start()

def main():
	wifi_name = get_wifi_name()


	while True:
		if not network_works():
			lcd.write('Connecting to {} '.format(wifi_name), 0)
			time.sleep(1)
			continue

		lcd.write('Connected {} (127.0.0.1) '.format(wifi_name), 0)
		lcd.write('User: {} '.format(username), 1)

		for f in os.listdir(waiting_to_upload_dir):
			try:
				lcd.write('Uploading: {} '.format(f), 1)
				Task(os.path.join(waiting_to_upload_dir, f)).handle()
				lcd.write('Uploaded: {} '.format(f), 1)
			except Exception as e:
				logging.exception('error uploading session')
				lcd.write('Uploading failed: {} '.format(e), 1)
				time.sleep(10)

		time.sleep(1)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		sys.exit(0)
