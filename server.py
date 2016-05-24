#! /usr/bin/python2
import tornado
import tornado.ioloop
import tornado.web
import os, uuid

from rolling_shutter import rolling_shutter

UPLOAD_DIR = "upload/"
BUF_SIZE = 4096


class Userform(tornado.web.RequestHandler):
    def get(self):
        self.render("form.html")


class Upload(tornado.web.RequestHandler):
    def post(self):
        file_info = self.request.files['filearg'][0]
        extn = os.path.splitext(file_info['filename'])[1]
        name = str(uuid.uuid4())

        path_src = UPLOAD_DIR + name + "_src" + extn
        path_dst = UPLOAD_DIR + name + "_dst" + ".avi"

        print path_src, path_dst

        fh = open(path_src, 'wb')
        fh.write(file_info['body'])
        fh.close()
        rolling_shutter(path_src, result_filename=path_dst)

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + file_info['filename'])
        with open(path_dst, 'r') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                self.write(data)
        os.remove(path_src)
        os.remove(path_dst)
        self.finish()


application = tornado.web.Application([
        (r"/", Userform),
        (r"/upload", Upload),
        ], debug=True)


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
