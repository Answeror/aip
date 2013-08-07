#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ..queue import EventQueue
from nose.tools import assert_equal
import time


def test_pop():
    q = EventQueue(1024)
    for i in range(3):
        time.sleep(0.1)
        q.push(i)
    assert_equal(q.pop(milliseconds=50), [2])
    assert_equal(q.pop(milliseconds=150), [1, 2])
    assert_equal(q.pop(milliseconds=250), [0, 1, 2])


def test_limit():
    q = EventQueue(3)
    for i in range(4):
        q.push(i)
    assert_equal(q.pop(seconds=1), [1, 2, 3])
