import re
import os
import flock
import logging
import requests
import socket
import fcntl
import struct
import time

wifi_re = re.compile(r'\s+wpa-ssid \"(.+)\"')


def iterfile(filename, offset):
    with open(filename, 'rb') as f:
        f.seek(offset)
        _attempts = 0

        while True:
            where = f.tell()
            d = f.read()

            if len(d) != 0:
                _attempts = 0
                yield d
            else:
                f.seek(where)

                if _attempts > 5:
                    break
                
                time.sleep(0.1)
                _attempts += 1 


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