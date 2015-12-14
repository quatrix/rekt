#!/usr/bin/env python

import os
import subprocess
import requests
import time
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

waiting_to_upload_dir = '/rec/to_upload/'
done_dir = '/rec/done'


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
		url = 'http://edisdead.com:55666/upload/{}/'.format(os.path.basename(self.session_dir))

		multiple_files = [
			('files', ('session.mp3', open(self.session_file, 'rb'), 'audio/mpeg')),
			('files', ('metadata.json', open(self.metadata_file, 'rb'), 'application/json'))
		]

		r = requests.post(url, files=multiple_files)

		if r.status_code != 200:
			raise RuntimeError('{} - failed to upload to server: {}'.format(self.session_file, r.text))

		logging.info('done uploading %s', self.session_dir)

	def move_to_done(self):
		os.rename(self.session_dir, os.path.join(done_dir, os.path.basename(self.session_dir)))
		

def main():
	while True:
		for f in os.listdir(waiting_to_upload_dir):
			try:
				Task(os.path.join(waiting_to_upload_dir, f)).handle()
			except Exception:
				logging.exception('error uploading session')

		time.sleep(1)

if __name__ == '__main__':
	main()
