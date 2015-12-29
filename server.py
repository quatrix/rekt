import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
from tornado.options import define, options
import json

from peewee import *

db = SqliteDatabase('sessions.db')

class Session(Model):
    id = PrimaryKeyField()
    username = CharField()
    session = DateField()
    markers = CharField()
    slices = CharField()

    class Meta:
        database = db

upload_dir = '/usr/share/nginx/html/rekt/uploads'


db.connect()
db.create_tables([Session], True)

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Depth, User-Agent, X-File-Size, X-Requested-With, X-Requested-By, If-Modified-Since, X-File-Name, Cache-Control")

    def options(self, *args, **kwargs):
        self.finish()
            

class UploadHandler(BaseHandler):
    def post(self, username):
        session_dir = os.path.join(upload_dir, username)

        if not os.path.exists(session_dir):
            os.mkdir(session_dir)

        session_file = self.request.files['files[session]'][0]
        metadata_file = self.request.files['files[metadata]'][0]
        metadata = json.loads(metadata_file['body'])

        with open(os.path.join(session_dir, '{}.mp3'.format(metadata['session'])), 'wb') as f:
            f.write(session_file['body'])

        # FIXME do a proper insert or update
        try:
            Session.get((Session.username == username) & (Session.session == metadata['session'])).delete_instance()
        except Exception:
            print("doesn't exist: {}".format(metadata['session']))
            pass

        Session(
            username=username,
            session=metadata['session'],
            markers=','.join((str(marker) for marker in metadata['markers'])),
            slices='',
        ).save()

        self.finish('done')


class SessionHandler(BaseHandler):
    def get(self, username, id):
        if id:
            sessions = Session.select().where((Session.username == username) & (Session.id == id))
        else:
            sessions = Session.select().where(Session.username == username)

        res = [{
            'id': session.id,
            'createdDate': session.session,
            'markers': [float(marker) for marker in session.markers.split(',') if marker],
            'slices': [[float(s) for s in sls.split(',')] for sls in session.slices.split('|') if sls],
            'audioUrl': 'http://edisdead.com/rekt/uploads/{}/{}.mp3'.format(username, session.session),
        } for session in sessions]


        self.finish({'res': res})

    def delete(self, username, id):
        Session.get((Session.username == username) & (Session.id == id)).delete_instance()


class SliceHandler(BaseHandler):
    def put(self, username, id):
        req = json.loads(self.request.body)

        slices = '|'.join([','.join([str(start_end['start']), str(start_end['end'])]) for start_end in req['slices']])

        Session.update(slices = slices).where((Session.username == username) & (Session.id == id)).execute()
        self.finish({'status': 'ok'})


def main():
    app = tornado.web.Application([
        (r"/upload/(.+)", UploadHandler),
        (r"/sessions/([^/]+)(?:/([0-9]+))?", SessionHandler),
        (r"/slices/(.+)/([0-9]+)", SliceHandler),
    ], debug=True, max_buffer_size=50000000)

    tornado.log.enable_pretty_logging()

    server = tornado.httpserver.HTTPServer(app, max_buffer_size=1024*1024*500)
    server.listen(55666)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
