# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math
from collections import deque
__author__ = 'ecialo'


def cut(size):
    def f(frame):
        h, w = frame.shape
        return frame[(h-size)/2:(h+size)/2, (w-size)/2:(w+size)/2]
    return f


def resize_and_cut(size, scale):
    def f(frame):
        h, w = frame.shape
        h, w = int(h*scale), int(w*scale)
        new_frame = cv2.resize(frame, (w, h))
        result = new_frame[(h-size)/2:(h+size)/2, (w-size)/2:(w+size)/2]
        return result
    return f


def make_rolling_frame(size, roughness):
    def f(frames):
        head = np.vstack([frame[roughness*i:roughness*(i+1), :] for i, frame in enumerate(frames)])
        try:
            h, w = head.shape
        except ValueError:
            head = head.reshape((roughness, head.shape[0]))
            h, w = head.shape
        tail = np.zeros((size - h, w), head.dtype)
        res = np.concatenate((head, tail))
        return res
    return f


def add_frame_to_frames(size):
    def f(frames, frame):
        if len(frames) >= size:
            frames.popleft()
        frames.append(frame)
    return f


def configure_tools(frame, roughness, scale, maxsize, framerate, result_filename):
    maxsize = maxsize or int(min(frame.shape)*scale)
    stack_size = int(math.ceil(float(maxsize)/roughness))

    appender = add_frame_to_frames(stack_size)
    composer = make_rolling_frame(maxsize, roughness)
    cutter = resize_and_cut(maxsize, scale)

    r, g, b = deque(), deque(), deque()
    result_video = cv2.VideoWriter(
        result_filename,
        cv2.cv.FOURCC(*'mp4v'),
        # cv2.cv.FOURCC(*'xvid'),
        # cv2.cv.FOURCC(*'MJPG'),
        # cv2.cv.FOURCC('P','I','M','1'),
        framerate,
        (maxsize, maxsize),     # Ломается при неквадратных видео из-за бага в opencv
    )

    return maxsize, appender, composer, cutter, r, g, b, result_video


def unblockable_rolling_shutter(filename, roughness=1, scale=1.0, maxsize=None, framerate=25, result_filename=None):
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
    result_filename = result_filename or filename.split(".")[0] + "_lagged.avi"
    result_video = None
    r, g, b = None, None, None
    is_configured = False
    frame_counter = 0

    cutter, appender, composer = None, None, None

    while True:
        is_success, frame = video.read()
        frame_counter += 1
        if frame_counter % 100 == 0:
            print frame_counter
        if is_success:
            channels = cv2.split(frame)
            if not is_configured:
                maxsize, appender, composer, cutter, r, g, b, result_video = configure_tools(
                    channels[0], roughness, scale, maxsize, framerate, result_filename
                )
                is_configured = True
            new_b, new_g, new_r = map(cutter, channels)
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
    for i in xrange(int(math.ceil(float(maxsize)/roughness))):
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


def rolling_shutter(filename, roughness=1, scale=1.0, maxsize=None, framerate=25, result_filename=None):
    reduce(lambda _, __: None, unblockable_rolling_shutter(filename, roughness, scale, maxsize, framerate, result_filename), None)


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