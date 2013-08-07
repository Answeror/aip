#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ..background import Background
from collections import deque
from nose.tools import assert_equal
from functools import partial


def test_action():
    b = Background(slave_count=3)
    b.start()
    q = deque()
    for i in range(3):
        b.action(lambda: q.append(0))
    b.stop()
    assert_equal(len(q), 3)


def test_function():
    b = Background(slave_count=3)
    b.start()
    q = deque()
    for i in range(3):
        b.function(partial(int, i), lambda x: q.append(x))
    b.stop()
    assert_equal(sorted(list(q)), list(range(3)))
