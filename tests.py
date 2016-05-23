# -*- coding: utf-8 -*-
import unittest as utst
import numpy as np
from rolling_shutter import make_rolling_frame
__author__ = 'ecialo'

SIZE = 6


class TestRollingFrame(utst.TestCase):

    def setUp(self):
        self.frames = [np.ones((6, 6)) * i for i in xrange(SIZE)]

    def tearDown(self):
        self.frames = None

    def testLine(self):
        """
        0 0 0 0 0 0
        1 1 1 1 1 1
        2 2 2 2 2 2
        3 3 3 3 3 3
        4 4 4 4 4 4
        5 5 5 5 5 5
        6 6 6 6 6 6
        """
        f = make_rolling_frame(SIZE, 1)
        et = np.array([[i for _ in xrange(SIZE)] for i in xrange(SIZE)])
        self.assertTrue((f(self.frames) == et).all())

    def testDoubleLine(self):
        """
        0 0 0 0 0 0
        0 0 0 0 0 0
        1 1 1 1 1 1
        1 1 1 1 1 1
        2 2 2 2 2 2
        2 2 2 2 2 2
        """
        f = make_rolling_frame(SIZE, 2)
        et = np.array([[i for _ in xrange(SIZE)] for i in sorted([q % 3 for q in xrange(SIZE)])])
        m = f(self.frames[:3:])
        self.assertTrue((m == et).all(), str(m))

    def testTripleLine(self):
        """
        0 0 0 0 0 0
        0 0 0 0 0 0
        0 0 0 0 0 0
        1 1 1 1 1 1
        1 1 1 1 1 1
        1 1 1 1 1 1
        """
        f = make_rolling_frame(SIZE, 3)
        et = np.array([[i for _ in xrange(SIZE)] for i in sorted([q % 2 for q in xrange(SIZE)])])
        m = f(self.frames[:2:])
        self.assertTrue((m == et).all(), str(m))

    def testQuadLine(self):
        """
        0 0 0 0 0 0
        0 0 0 0 0 0
        0 0 0 0 0 0
        0 0 0 0 0 0
        1 1 1 1 1 1
        1 1 1 1 1 1
        """
        f = make_rolling_frame(SIZE, 4)
        et = np.array([
            [0 for _ in xrange(SIZE)],
            [0 for _ in xrange(SIZE)],
            [0 for _ in xrange(SIZE)],
            [0 for _ in xrange(SIZE)],
            [1 for _ in xrange(SIZE)],
            [1 for _ in xrange(SIZE)],
        ])
        m = f(self.frames[:2:])
        self.assertTrue((m == et).all(), str(m))

if __name__ == '__main__':
    suite = utst.makeSuite(TestRollingFrame)
    utst.TextTestRunner(verbosity=2).run(suite)