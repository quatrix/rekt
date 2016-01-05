from tornado.web import Application
from tornado import gen
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.log import enable_pretty_logging
from tornado.options import parse_command_line, define, options
from base_handler import BaseHandler
from upload_handler import UploadHandler
from stream_handler import StreamHandler


import motor
import click
import logging
import json
import os


define('port', default=55666)
define('debug', default=True)
define('server_delay', default=0.5)
define('upload_dir', default='/usr/share/nginx/html/rekt/uploads')


def create_stream_url(username, id):
    return 'http:///stream/{}/{}.mp3'.format(username, id)


class SessionHandler(BaseHandler):
    @gen.coroutine
    def get(self, username, id):
        coll = self.settings['db'].sessions

        if id:
            cursor = coll.find({
                'username': username,
                'id': id,
            })
        else: 
            cursor = coll.find({'username': username}).sort('id')

        res = (yield cursor.to_list(None))

        for i in res:
            del i['_id']
            i['stream'] = create_stream_url(username, i['id'])

        self.finish({'res': res})

    @gen.coroutine
    def put(self, username, id):
        logging.info('updating for %s (%s)', username, id)
        coll = self.settings['db'].sessions

        req = json.loads(self.request.body)

        d = {
            'username': username,
            'id': id,
        }

        session = yield coll.find_one(d)

        if session is None:
            logging.info('insert')
            d.update(req)
            yield coll.insert(d)
        elif req:
            logging.info('update')
            yield coll.update(d, {'$set': req})

        self.finish({'status': 'ok'})

    @gen.coroutine
    def delete(self, username, id):
        logging.info('updating for %s (%s)', username, id)
        coll = self.settings['db'].sessions

        d = {
            'username': username,
            'id': id,
        }

        yield coll.remove(d)

        self.finish({'status': 'ok'})


def main():
    db = motor.motor_tornado.MotorClient().rekt

    parse_command_line()

    app = Application([
        (r"/sessions/([^/]+)(?:/([0-9]+))?", SessionHandler),
        (r"/upload/(.+)/([0-9]+)", UploadHandler),
        (r"/stream/(.+)/([0-9]+)", StreamHandler),
    ], debug=options.debug, db=db)

    enable_pretty_logging()

    server = HTTPServer(app, max_buffer_size=1024*1024*500)
    server.listen(options.port)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
