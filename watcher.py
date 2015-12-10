import os
import subprocess
import requests


waiting_to_upload_dir = '/rec/to_upload/'
done_dir = '/rec/done'


class Task(object):
	def __init__(self, session_dir):
		self.session_dir = session_dir
		self.session_file = os.path.join(session_dir, 'session.wav')
		self.metadata_file = os.path.join(session_dir, 'metadata.json')
		self.compressed_file = os.path.join(session_dir, 'session.mp3')

	def check_sanity(self):
		if not os.path.exists(self.session_file):
			raise RuntimeError('{} - session file missing'.format(self.session_file))

		if not os.path.exists(self.metadata_file):
			raise RuntimeError('{} - metadata file missing'.format(self.metadata_file))

	def handle(self):
		self.check_sanity()
		self.compress_session()
		self.upload_session()
		
	def compress_session(self):
		if os.path.exists(self.compressed_file):
			return

		compressed_file_tmp = os.path.join(self.session_dir, 'session.mp3.tmp')
		rc = subprocess.call(['lame', '-V0', self.session_file, compressed_file_tmp])

		if rc != 0:
			raise RuntimeError('{} - compression failed, return code: {}'.format(self.session_dir, rc))

		os.rename(compressed_file_tmp, self.compressed_file)

	def upload_session(self):
		url = 'http://edisdead.com:55666/upload/{}/'.format(os.path.basename(self.session_dir))

		multiple_files = [
			('files', ('session.mp3', open(self.compressed_file, 'rb'), 'audio/mpeg')),
			('files', ('metadata.json', open(self.metadata_file, 'rb'), 'application/json'))
		]

		r = requests.post(url, files=multiple_files)
		print(r.text)
		

def main():
	for f in os.listdir(waiting_to_upload_dir):
		Task(os.path.join(waiting_to_upload_dir, f)).handle()


if __name__ == '__main__':
	main()
