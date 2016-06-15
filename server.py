#! /usr/bin/python2
# -*- coding: utf-8 -*-
import tornado
import tornado.ioloop
from tornado import gen
from tornado.queues import Queue
import tornado.web
import os, uuid, random, string, json
from rolling_shutter import unblockable_rolling_shutter

UPLOAD_DIR = "upload/"
BUF_SIZE = 4096
SID_LEN = 32


q = Queue()
task_list = []


def sid_gen():
    return ''.join(random.SystemRandom().choice(string.hexdigits) for _ in range(SID_LEN))


def get_tasks_info(sid):
    tasks = []
    for task in task_list:
        if not task["sid"] == sid:
            continue
        tasks.append({
            "id": task["id"],
            "name": task["name"],
            "state": task["state"],
            "progress": task["progress"],
        })
    return tasks


@gen.coroutine
def watch_queue():
    while True:
        item = yield q.get()
        # TODO: drop failed tasks
        try:
            item["state"] = 1
            while True:
                item["gen"].next()
                yield gen.moment
        except StopIteration:
            item["state"] = 2
            print "processing completed"
        finally:
            q.task_done()


class Userform(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        tasks = []

        sid = self.get_cookie("sid")
        if sid:
            tasks = get_tasks_info(sid)

        self.render("form.html", tasks=tasks)

    @gen.coroutine
    def post(self):

        sid = self.get_cookie("sid")
        if not sid:
            sid = sid_gen()
            self.set_cookie("sid", sid)

        task_id = str(uuid.uuid4())

        # TODO: Catch exceptions and delete bad sources

        file_info = self.request.files['filearg'][0]
        extn = os.path.splitext(file_info['filename'])[1]

        path_src = UPLOAD_DIR + task_id + "_src" + extn
        path_dst = UPLOAD_DIR + task_id + "_dst" + ".avi"

        print path_src, path_dst

        fh = open(path_src, 'wb')
        fh.write(file_info['body'])
        fh.close()

        roughness = int(self.get_argument("roughness", 1))
        scale = float(self.get_argument("scale", 1))

        handler = unblockable_rolling_shutter(path_src, result_filename=path_dst, roughness=roughness, scale=scale)
        info = {
            "gen": handler,
            "sid": sid,
            "id": task_id,
            "src": path_src,
            "dst": path_dst,
            "name": file_info['filename'],
            "state": 0,  # set 1 when task is first in queue, set 2 when processing is completed
            "progress": 0,  # from 0 to 100
        }
        task_list.append(info)
        q.put(info)
        print "processing started..."

        self.redirect("./")


class GetStats(tornado.web.RequestHandler):
    def get(self):
        sid = self.get_cookie("sid")
        tasks = get_tasks_info(sid)

        self.finish(json.dumps(tasks))


class GetFile(tornado.web.RequestHandler):
    def get(self):
        sid = self.get_cookie("sid")
        task_id = self.get_argument("id")

        for task in task_list:
            if not task["id"] == task_id:
                continue

            if not task["sid"] == sid:
                self.set_status(403)
                self.finish("<html><body>403: FORBIDDEN</body></html>")

            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename=' + task["name"])
            with open(task["dst"], 'rb') as f:
                data = f.read()
                self.write(data)
            self.finish()
            task_list.remove(task)
            os.remove(task["src"])
            os.remove(task["dst"])
            return

        self.set_status(404)
        self.finish("<html><body>404: NOT FOUND</body></html>")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8081)
    parser.add_argument("-a", "--address", type=str, default='127.0.0.1')
    args = parser.parse_args()

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "debug": True,
    }
    application = tornado.web.Application([
        (r"/", Userform),
        (r"/stats", GetStats),
        (r"/file", GetFile),
        (r"/static/(.*)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
    ], **settings)
    application.listen(args.port, address=args.address)

    tornado.ioloop.IOLoop.instance().add_callback(watch_queue)
    tornado.ioloop.IOLoop.instance().start()
