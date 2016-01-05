from tornado.websocket import WebSocketHandler
from tornado.options import options
from tornado import gen

import logging
import os


class StreamHandler(WebSocketHandler):
    def open(self, username, id):
        print("WebSocket opened")
        filepath = os.path.join(options.upload_dir, username, id + '.mp3')
        self._fh = open(filepath)

    def on_message(self, message):
        b = self._fh.read(1024 * 100)

        if len(b) != 0:
            logging.info('sending %d bytes', len(b))
            self.write_message(b, binary=True)

    def on_close(self):
        print("WebSocket closed")

    def check_origin(self, origin):
        return True
