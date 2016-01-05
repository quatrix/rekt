import re
import os
import flock
import logging
import requests
import socket
import fcntl
import struct

wifi_re = re.compile(r'\s+wpa-ssid \"(.+)\"')


def is_locked(filename):
	return os.path.exists(os.path.join('/var/lock', os.path.basename(filename)))


def lock_file(filename):
	open(os.path.join('/var/lock', os.path.basename(filename)), 'w')


def unlock_file(filename):
	lockfile = os.path.join('/var/lock', os.path.basename(filename))

	if os.path.exists(lockfile):
		os.unlink(lockfile)


def iterfile(filename, offset):
	with open(filename, 'rb') as f:
		f.seek(offset)

		while True:
			where = f.tell()
			d = f.read()

			if len(d) != 0:
				yield d
			else:
				f.seek(where)

				if not is_locked(filename):
					logging.info('%s not locked, done reading')
					break
			


def get_wifi_name(work_dir):
	for l in open(os.path.join(work_dir, 'config/wifi')).readlines():
		r = wifi_re.search(l)

		if r:
			return r.group(1)


def is_connected():
	try:
		return requests.get('http://edisdead.com').status_code == 200
	except Exception:
		logging.exception('is connected')
		return False



def get_local_ip():
	for interface in 'wlan0', 'en0', 'lo0':
		try:
			return get_ip_address('wlan0')
		except IOError:
			pass
		

def get_username(work_dir):
	return open(os.path.join(work_dir, 'config/username')).read().strip()


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def scrolling_text(text, chars):
	while True:
		if len(text) <= chars:
			yield text
		else:
			yield text[:chars-1]
			text = text[1:] + text[0]
