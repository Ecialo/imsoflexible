#! /usr/bin/python2
# -*- coding: utf-8 -*-
import tornado
import tornado.ioloop
from tornado import gen
from tornado.queues import Queue
import tornado.web
import os, uuid
from rolling_shutter import unblockable_rolling_shutter

UPLOAD_DIR = "upload/"
BUF_SIZE = 4096


q = Queue()


@gen.coroutine
def watch_queue():
    while True:
        item = yield q.get()
        try:
            item.next()
            yield gen.moment
            q.put(item)
        except StopIteration:
            print "processing completed"
        finally:
            q.task_done()


class Userform(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        self.render("form.html")


class Upload(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self):

        # TODO: Catch exceptions and delete bad sources

        file_info = self.request.files['filearg'][0]
        extn = os.path.splitext(file_info['filename'])[1]
        name = str(uuid.uuid4())

        path_src = UPLOAD_DIR + name + "_src" + extn
        path_dst = UPLOAD_DIR + name + "_dst" + ".avi"

        print path_src, path_dst

        fh = open(path_src, 'wb')
        fh.write(file_info['body'])
        fh.close()

        roughness = int(self.get_argument("roughness", 1))
        scale = float(self.get_argument("scale", 1))

        q.put(unblockable_rolling_shutter(path_src, result_filename=path_dst, roughness=roughness, scale=scale))
        print "processing started..."

        # self.set_header('Content-Type', 'application/octet-stream')
        # self.set_header('Content-Disposition', 'attachment; filename=' + file_info['filename'])
        # with open(path_dst, 'r') as f:
        #     while True:
        #         data = f.read(BUF_SIZE)
        #         if not data:
        #             break
        #         self.write(data)
        # os.remove(path_src)
        # os.remove(path_dst)
        self.finish()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8081)
    parser.add_argument("-a", "--address", type=str, default='127.0.0.1')
    args = parser.parse_args()

    tornado.ioloop.IOLoop.instance().add_callback(watch_queue)
    application = tornado.web.Application([
        (r"/", Userform),
        (r"/upload", Upload),
    ], debug=True)
    application.listen(args.port, address=args.address)
    tornado.ioloop.IOLoop.instance().start()
