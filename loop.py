#!/usr/bin/env python
from threading import Thread, Event
from utils import get_username

import RPi.GPIO as GPIO
import subprocess
import logging
import json
import time
import os
import re
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

pedal = 18

led_red = 16
led_blue = 20
led_green = 21

led_rgb = [led_red, led_blue, led_green]

led_peak = 26

work_dir = '/rec'
upload_dir = '/rec/to_upload'
hold_time = 1.2 #seconds
peak_meter_re = re.compile(r'\| (\d\d)\%')

prev_buffer = ['']

def get_peak_vu_meter(pipe):
		d = pipe.read(50)
		r = peak_meter_re.search(prev_buffer[0] + d)
		prev_buffer[0] = d

		if r:
			return r.group(1)


class Recorder(object):
	def __init__(self):
		self.recording = False
		self.setup_hardware()
		self.last_pedal_press = None

	def setup_hardware(self):
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(pedal, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(led_rgb, GPIO.OUT)
		GPIO.setup(led_peak, GPIO.OUT)
		GPIO.add_event_detect(pedal, GPIO.RISING, callback=self.on_pedal_change, bouncetime=50)
		self.make_rgb_green()

	def on_pedal_change(self, channel):
		time.sleep(0.02)

		if not GPIO.input(channel):
			return

		if self.last_pedal_press is not None and time.time() - self.last_pedal_press < 0.2:
			return

		logging.info('pedal change: %d', channel)

		t0 = time.time()

		while GPIO.input(channel):
			self.last_pedal_press = time.time()
			
			if self.last_pedal_press - t0 > hold_time:
				break;

			time.sleep(0.01)

		if time.time() - t0 > hold_time:
			self.toggle_rec()
		elif self.recording:
			self.set_mark()

		self.last_pedal_press = time.time()

	def make_rgb_green(self):
		self.turn_rgb_off()
		GPIO.output(led_green, 0)

	def make_rgb_red(self):
		self.turn_rgb_off()
		GPIO.output(led_red, 0)

	def make_rgb_purple(self):
		self.turn_rgb_off()
		GPIO.output(led_red, 0)
		GPIO.output(led_blue, 0)

	def turn_rgb_off(self):
		for led in led_rgb:
			GPIO.output(led, 1)

	def toggle_rec(self):
		if self.recording:
			self.stop_recording()
		else:
			self.start_recording()

		self.recording = not self.recording

	def create_session(self):
		self.session_start_time = int(time.time())
		self.session_file = os.path.join(upload_dir, '{}.mp3'.format(self.session_start_time))
		self.metadata_file = os.path.join(upload_dir, '{}.json'.format(self.session_start_time))

	@property
	def time_since_session_started(self):
		return time.time() - self.session_start_time

	def record_from_mic(self):
		self.create_session()
		arecord_args = 'arecord -vv -D plughw:1,0 -f cd -t raw' 
		lame_args = 'lame -r -h --cbr -b 128 - {}'.format(self.session_file)

		self.arecord_process = subprocess.Popen(
			arecord_args.split(),
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
		)

		self.lame_process = subprocess.Popen(lame_args.split(), stdin=self.arecord_process.stdout)

		self.start_rec_monitor()

	def start_rec_monitor(self):
		self._monitor_stop = Event()
		self._monitor_thread = Thread(target=self.rec_monitor, args=())
		self._monitor_thread.start()

	def rec_monitor(self):
		while True:
			if self._monitor_stop.isSet():
				GPIO.output(led_peak, 0)
				return

			v = get_peak_vu_meter(self.arecord_process.stderr)

			if v is not None and int(v) > 95:
				GPIO.output(led_peak, 1)
			else:
				GPIO.output(led_peak, 0)

	def stop_rec_monitor(self):
		self._monitor_stop.set()
		self._monitor_thread.join()

	@property
	def metadata(self):
		return {
			'markers': self.markers,
		}

	def write_metadata_file(self):
		filename = self.metadata_file + '.tmp'

		with open(filename, 'w') as f:
			f.write(json.dumps(self.metadata, indent=4))

		os.rename(filename, self.metadata_file)

	def start_recording(self):
		logging.info('starting recording')
		self.markers = []
		self.record_from_mic()
		self.make_rgb_red()
		self.write_metadata_file()

	def stop_recording(self):
		logging.info('stopping recording')
		self.stop_rec_monitor()
		self.arecord_process.terminate()
		self.lame_process.terminate()

		self.write_metadata_file()
		self.make_rgb_green()

	def set_mark(self):
		logging.info('setting mark')
		self.markers.append(self.time_since_session_started)

		self.make_rgb_purple()
		time.sleep(0.2)
		self.make_rgb_red()
		self.write_metadata_file()

	def read_pedal(self):
		return GPIO.input(pedal)

	def serve(self):
		while True:
			time.sleep(999)	


def main():
	try:
		Recorder().serve()
	finally:
		GPIO.cleanup()


if __name__ == '__main__':
	main()
