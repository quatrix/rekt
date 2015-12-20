#!/usr/bin/env python

import os
import re
import subprocess
import requests
import time
import sys
import logging
import RPi_I2C_driver


# Print happy welcome message on lines 1 and 3

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

waiting_to_upload_dir = '/rec/to_upload/'
done_dir = '/rec/done'
username = open('/rec/config/username').read().strip()


class LCD(object):
	def __init__(self):
		self.lcd = RPi_I2C_driver.lcd()
		self._last_msg = None

	def clear(self):
		self.lcd.lcd_display_string(' '*16, 1)
		self.lcd.lcd_display_string(' '*16, 2)

	def write(self, msg):
		if msg == self._last_msg:
			return

		self._last_msg = msg

		self.clear()

		for l, s in enumerate(msg.split('\n', 1), 1):
			self.lcd.lcd_display_string(s, l)

lcd = LCD()

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
			('session', ('session.mp3', open(self.session_file, 'rb'), 'audio/mpeg')),
			('metadata', ('metadata.json', open(self.metadata_file, 'rb'), 'application/json'))
		]

		r = requests.post(url, files=multiple_files)

		if r.status_code != 200:
			raise RuntimeError('{} - failed to upload to server: {}'.format(self.session_file, r.text))

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


def main():
	wifi_name = get_wifi_name()

	while True:
		if not network_works():
			lcd.write('Connecting to\n{}'.format(wifi_name))
			time.sleep(1)
			continue

		lcd.write('Connected to\n{}'.format(wifi_name))

		for f in os.listdir(waiting_to_upload_dir):
			try:
				lcd.write('Uploading\n{}'.format(f))
				Task(os.path.join(waiting_to_upload_dir, f)).handle()
				lcd.write('Uploaded\n{}'.format(f))
			except Exception:
				logging.exception('error uploading session')
				lcd.write('Error uploading\n{}'.format(f))

		time.sleep(1)

if __name__ == '__main__':
	main()
