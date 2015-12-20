#!/usr/bin/env python

from __future__ import print_function

import RPi.GPIO as GPIO
import subprocess
import json
import time
import os

pedal = 18

led_red = 16
led_blue = 20
led_green = 21

led_rgb = [led_red, led_blue, led_green]

temp_dir = '/rec/temp'
done_dir = '/rec/to_upload'


hold_time = 1.2 #seconds

class Recorder(object):
	def __init__(self):
		self.recording = False
		self.setup_hardware()
		self.last_pedal_press = None

	def setup_hardware(self):
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(pedal, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(led_rgb, GPIO.OUT)
		GPIO.add_event_detect(pedal, GPIO.RISING, callback=self.on_pedal_change, bouncetime=50)
		self.make_rgb_green()

	def on_pedal_change(self, channel):
		time.sleep(0.02)

		if not GPIO.input(channel):
			return

		if self.last_pedal_press is not None and time.time() - self.last_pedal_press < 0.2:
			return

		print('pedal change', channel)

		t0 = time.time()

		while GPIO.input(channel):
			print('holding...')
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
		session = time.strftime("%d_%m_%y_%H_%M_%S", time.gmtime(self.session_start_time))
		self.session_dir = os.path.join(temp_dir, session)
		self.session_dir_done = os.path.join(done_dir, session)
		os.mkdir(self.session_dir)

	@property
	def time_since_session_started(self):
		return time.time() - self.session_start_time

	def record_from_mic(self):
		self.create_session()
		arecord_args = 'arecord -D plughw:1,0 -f cd -t raw' 
		lame_args = 'lame -r -h -V 0 - {}'.format(os.path.join(self.session_dir, 'session.mp3'))

		self.arecord_process = subprocess.Popen(arecord_args.split(), stdout=subprocess.PIPE)
		self.lame_process = subprocess.Popen(lame_args.split(), stdin=self.arecord_process.stdout)


	def start_recording(self):
		print('starting recording')
		self.markers = []
		self.record_from_mic()
		self.make_rgb_red()

	@property
	def metadata(self):
		return {
			'session': self.session_start_time,
			'markers': self.markers,
		}

	def stop_recording(self):
		print('stopping recording')
		self.arecord_process.terminate()
		self.lame_process.terminate()

		with open(os.path.join(self.session_dir, 'metadata.json'), 'w') as f:
			print(json.dumps(self.metadata, indent=4), file=f)

		os.rename(self.session_dir, self.session_dir_done)

		self.make_rgb_green()

	def set_mark(self):
		print('setting mark')
		self.markers.append(self.time_since_session_started)

		self.make_rgb_purple()
		time.sleep(0.2)
		self.make_rgb_red()

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
