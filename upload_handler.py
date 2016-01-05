from tornado.web import stream_request_body
from base_handler import BaseHandler
from tornado import gen
from tornado.options import options
from tornado.locks import Condition

import os
import logging

@stream_request_body
class UploadHandler(BaseHandler):
    _waiting_to_finish = {}

    def prepare(self):
        logging.info('UploadHandler.prepare')
        s = self.request.path.split('/')

        username = s[2]
        session_id = s[3]

        self.upload_path = os.path.join(options.upload_dir, username, session_id + '.mp3')

        if self.request.method == "POST":
            logging.info('hey')
                    
            self.__class__._waiting_to_finish[self.upload_path] = Condition()
            upload_dir = os.path.join(options.upload_dir, username)

            if not os.path.isdir(upload_dir):
                os.mkdir(upload_dir)

            if self.request.query == 'override=1':
                self._fh = open(self.upload_path, 'wb+')
            else:
                self._fh = open(self.upload_path, 'ab+')

    @gen.coroutine
    def data_received(self, chunk):
        logging.info('UploadHandler.data_received(%d bytes: %r)', len(chunk), chunk[:9])
        self._fh.write(chunk)

    def on_finish(self):
        if self.request.method == "POST":
            uploading = self.__class__._waiting_to_finish.get(self.upload_path)
            uploading.notify()
            del self.__class__._waiting_to_finish[self.upload_path]

    def on_connection_close(self):
        if self.request.method == "POST":
            self.on_finish()

    @gen.coroutine
    def post(self, username, id):
        logging.info('UploadHandler.post done')
        coll = self.settings['db'].sessions

        d = {
            'username': username,
            'id': id,
        }

        session = yield coll.find_one(d)

        if session is None:
            yield coll.insert(d)

        self.finish('ok')

    @gen.coroutine
    def get(self, *args):
        uploading = self.__class__._waiting_to_finish.get(self.upload_path)

        if uploading:
            logging.info('waiting for upload to finish: %s', self.upload_path)
            yield uploading.wait()

        try:
            size = os.path.getsize(self.upload_path)
        except OSError:
            size = 0

        logging.info('upload.get offset: %d', size)
        self.finish(str(size))
