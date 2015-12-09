# program starts indicator led is green
# register start/stop recording button event handler
# when event fires:
# * if not recording:
#   0. create a session dir (based on timestamp)
#	1. start recording
#   2. turn indicator led to red
#   3. register marker button event handler
# * if recording:
#	1. stop recording
#   2. turn indicator light to initial state
#   3. unregister marker button event handler
#   4. move session dir to the upload folder
# marker button event handler:
#	should only fire while in recording state,
#   append a new line to the markers.txt file in the session dir
#   new line contains timestamp,id (registered with the button)
# when idle:
# check if there's something to upload, if so:
#	1. upload it
#   2. move it to 'uploaded' dir

import RPi.GPIO as GPIO
from time import sleep

toggle_rec_btn = 18
marker_btn = 17

input_channels = [toggle_rec_btn, marker_btn]

led_red = 16
led_blue = 20
led_green = 21

led_rgb = [led_red, led_blue, led_green]


class Recorder(object):
	def __init__(self):
		self.recording = False
		self.setup_hardware()

	def setup_hardware(self):
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(input_channels, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(led_rgb, GPIO.OUT)
		GPIO.add_event_detect(toggle_rec_btn, GPIO.FALLING, callback=self.handle_toggle_rec, bouncetime=400)
		self.make_rgb_green()

	def make_rgb_green(self):
		self.turn_rgb_off()
		GPIO.output(led_green, 0)

	def make_rgb_red(self):
		self.turn_rgb_off()
		GPIO.output(led_red, 0)

	def turn_rgb_off(self):
		for led in led_rgb:
			GPIO.output(led, 1)

	def handle_toggle_rec(self, *args, **kwargs):
		if self.recording:
			self.stop_recording()
		else:
			self.start_recording()

		self.recording = not self.recording

	def start_recording(self):
		print('starting recording')
		GPIO.add_event_detect(marker_btn, GPIO.FALLING, callback=self.handle_marker, bouncetime=200)
		self.make_rgb_red()

	def stop_recording(self):
		print('stopping recording')
		GPIO.remove_event_detect(marker_btn)
		self.make_rgb_green()

	def handle_marker(self, *args):
		print('setting mark')

	def serve(self):
		while True:
			sleep(999)


def main():
	try:
		Recorder().serve()
	finally:
		GPIO.cleanup()


if __name__ == '__main__':
	main()
