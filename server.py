import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
from tornado.options import define, options

upload_dir = '/usr/share/nginx/html/rekt/uploads'

class UploadHandler(tornado.web.RequestHandler):
    def post(self, session):
        session_dir = os.path.join(upload_dir, session)

        if not os.path.exists(session_dir):
            os.mkdir(session_dir)

        for uploaded_file  in self.request.files['files']:
            with open(os.path.join(session_dir, uploaded_file['filename']), 'wb') as f:
                f.write(uploaded_file['body'])

        self.finish('done')

def main():
    application = tornado.web.Application([
        (r"/upload/(.+)/", UploadHandler)
    ], debug=True)

    application.listen(55666)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
