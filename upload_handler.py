from tornado.web import stream_request_body, HTTPError
from tornado.options import options
from tornado import gen

from base_handler import BaseHandler

import os
import logging
import httplib

@stream_request_body
class UploadHandler(BaseHandler):
    _uploading = set()

    @gen.coroutine
    def create_session_in_db(self):
        coll = self.settings['db'].sessions

        d = {
            'username': self.username,
            'id': self.session_id,
        }

        session = yield coll.find_one(d)

        if session is None:
            yield coll.insert(d)

    def prepare_file_handlers(self):
        upload_dir = os.path.join(options.upload_dir, self.username)

        if not os.path.isdir(upload_dir):
            os.mkdir(upload_dir)

        if self.upload_override:
            self._fh = open(self.upload_path, 'wb+')
        else:
            self._fh = open(self.upload_path, 'ab+')

    def parse_request(self):
        s = self.request.path.split('/')

        self.username = s[2]
        self.session_id = s[3]
        self.upload_path = os.path.join(options.upload_dir, self.username, self.session_id + '.mp3')
        self.upload_override = self.request.query == 'override=1'

    @gen.coroutine
    def prepare(self):
        logging.info('UploadHandler.prepare')
        self.parse_request()

        if self.currently_being_uploaded:
            raise HTTPError(400, 'currently being uploaded')

        if self.request.method == "POST":
            self.set_being_uploaded()
            self.prepare_file_handlers()
            yield self.create_session_in_db()

    @gen.coroutine
    def data_received(self, chunk):
        logging.info('UploadHandler.data_received(%d bytes: %r)', len(chunk), chunk[:9])
        self._fh.write(chunk)

    def on_finish(self):
        if self.request.method == "POST":
            self.unset_being_uploaded()

    def on_connection_close(self):
        self.on_finish()

    @gen.coroutine
    def post(self, *args):
        logging.info('UploadHandler.post done')
        self.finish('ok')

    @gen.coroutine
    def get(self, *args):
        try:
            size = os.path.getsize(self.upload_path)
        except OSError:
            size = 0

        self.finish(str(size))

    @property
    def currently_being_uploaded(self):
        return self.upload_path in self.__class__._uploading

    def set_being_uploaded(self):
        self.__class__._uploading |= set([self.upload_path])

    def unset_being_uploaded(self):
        self.__class__._uploading -= set([self.upload_path])

