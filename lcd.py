from utils import scrolling_text

class FakeLCDManager(object):
	def write(self, msg, line):
		#print(msg, line)
		pass

	def start(self):
		pass

	def stop(self):
		pass


class LCDManager(object):
	def __init__(self):
		self.q = Queue()
		self.lcd = LCD()
		self.time_of_last_update = 0;
		self._stop = Event()

	def run(self):
		while True:
			if self._stop.isSet():
				return

			try:
				command = self.q.get_nowait()
				msg, line = command
				self.lcd.set(msg, line)
			except Empty:
				pass

			if time.time() - self.time_of_last_update > 0.7:
				self.lcd.update()
				self.time_of_last_update = time.time()

			time.sleep(0.01)

	def write(self, msg, line):
		self.q.put((msg ,line))

	def start(self):
		self._t = Thread(target=self.run, args=())
		self._t.start()

	def stop(self):
		self._stop.set()
		return self._t.join()


class LCD(object):
	def __init__(self, chars=16, lines=2):
		import RPi_I2C_driver

		self.lcd = RPi_I2C_driver.lcd()
		self.chars = chars
		self.lines = [None for _ in xrange(lines)]
		self._lines_text = [None for _ in xrange(lines)]
		self._cache = [None for _ in xrange(lines)]

	def set(self, text, line):
		if self._lines_text[line] == text:
			return

		self._lines_text[line] = text
		self.lines[line] = scrolling_text(text, self.chars)

	def clear_line(self, line):
		self.lcd.lcd_display_string(' '*self.chars, line+1)

	def write_to_lcd(self, text, line):
		if self._cache[line] != text:
			self.clear_line(line)
			self.lcd.lcd_display_string(text, line+1)
			self._cache[line] = text

	def update(self):
		for line, generator in enumerate(self.lines):
			if generator is None:
				continue

			self.write_to_lcd(next(generator), line)
