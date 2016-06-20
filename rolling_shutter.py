# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math
from collections import deque
__author__ = 'ecialo'


def resize(scale):
    def f(frame):
        h, w = frame.shape
        h, w = int(h*scale), int(w*scale)
        new_frame = cv2.resize(frame, (w, h))
        return new_frame
    return f


def make_rolling_frame(roughness):
    def f(frames):
        head = np.vstack([frame[roughness*i:roughness*(i+1), :] for i, frame in enumerate(frames)])
        try:
            h, w = head.shape
        except ValueError:
            head = head.reshape((roughness, head.shape[0]))
            h, w = head.shape
        tail = np.zeros((0, w), head.dtype)
        res = np.concatenate((head, tail))
        return res
    return f


def add_frame_to_frames(size):
    def f(frames, frame):
        if len(frames) >= size:
            frames.popleft()
        frames.append(frame)
    return f


def configure_tools(frame, roughness, scale, framerate, result_filename):
    h, w = frame.shape
    stack_size = int(math.ceil(float(h)/roughness))

    appender = add_frame_to_frames(stack_size)
    composer = make_rolling_frame(roughness)
    resizer = resize(scale)

    r, g, b = deque(), deque(), deque()
    result_video = cv2.VideoWriter(
        result_filename,
        cv2.cv.FOURCC(*'mp4v'),
        # cv2.cv.FOURCC(*'xvid'),
        # cv2.cv.FOURCC(*'MJPG'),
        # cv2.cv.FOURCC('P','I','M','1'),
        framerate,
        (int(w*scale), int(h*scale)),
    )

    return appender, composer, resizer, r, g, b, result_video


def unblockable_rolling_shutter(filename, roughness=1, scale=1.0, framerate=25, result_filename=None):
    """
    Накладывает на видео эффект rolling shatter и сохраняет результат

    Каждая строка из roughness пикселей каждого кадра обработанного виде опережает предыдущую строку на 1 кадр.
    :param filename: имя файла с видео
    :type filename: str
    :param roughness: размер фрагмента задержки в строках
    :type roughness: int
    :param scale: пространственный коэфициент сжатия кадров
    :type scale: float
    :param maxsize: максимальный размер кадра
    :type maxsize: int
    :return:
    :rtype:
    """
    video = cv2.VideoCapture(filename)
    h = video.get(4)

    result_filename = result_filename or filename.split(".")[0] + "_lagged.avi"
    result_video = None
    r, g, b = None, None, None
    is_configured = False
    frame_counter = 0

    resizer, appender, composer = None, None, None

    while True:
        is_success, frame = video.read()
        frame_counter += 1
        if frame_counter % 100 == 0:
            print frame_counter
        if is_success:
            channels = cv2.split(frame)
            if not is_configured:
                appender, composer, resizer, r, g, b, result_video = configure_tools(
                    channels[0], roughness, scale, framerate, result_filename
                )
                is_configured = True
            new_b, new_g, new_r = map(resizer, channels)
            appender(b, new_b)
            appender(g, new_g)
            appender(r, new_r)
            new_frame = cv2.merge([
                composer(b),
                composer(g),
                composer(r)
            ])
            result_video.write(new_frame)
            yield
        else:
            break
    for i in xrange(int(math.ceil(float(h)/roughness))):
        frame_counter += 1
        if frame_counter % 100 == 0:
            print "+"
        appender(b, new_b)
        appender(g, new_g)
        appender(r, new_r)
        new_frame = cv2.merge([
            composer(b),
            composer(g),
            composer(r)
        ])
        result_video.write(new_frame)
        yield
    video.release()
    result_video.release()


def rolling_shutter(filename, roughness=1, scale=1.0, framerate=25, result_filename=None):
    reduce(lambda _, __: None, unblockable_rolling_shutter(filename, roughness, scale, framerate, result_filename), None)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-r", "--roughness", type=int, default=1)
    parser.add_argument("-s", "--scale", type=float, default=1.0)
    parser.add_argument("-m", "--maxsize", type=int, default=None)
    parser.add_argument("-f", "--framerate", type=int, default=25),
    parser.add_argument("-rf", "--result_filename", default=None)
    args = parser.parse_args()
    # print args
    rolling_shutter(**args.__dict__)