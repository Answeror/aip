#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import assert_equal
from ..dag import Dag


def make():
    d = Dag()
    for i in range(5):
        d.add(i)
    for child, parent in (
        (2, 0),
        (3, 0),
        (3, 1),
        (4, 2),
        (4, 3)
    ):
        d.link(child, parent)
    return d


def test_dag():
    d = make()
    '''
       0   1
     / | /
    2  3
    | /
    4
    '''
    assert_equal(d.up, {
        0: set(),
        1: set(),
        2: set([0]),
        3: set([0, 1]),
        4: set([0, 1, 2, 3])
    })
    assert_equal(d.down, {
        0: set([2, 3, 4]),
        1: set([3, 4]),
        2: set([4]),
        3: set([4]),
        4: set()
    })
    d.remove(3)
    '''
       0   1
     /
    2
    |
    4
    '''
    assert_equal(d.up, {
        0: set(),
        1: set(),
        2: set([0]),
        4: set([0, 2])
    })
    assert_equal(d.down, {
        0: set([2, 4]),
        1: set([]),
        2: set([4]),
        4: set()
    })
    d.unlink(2, 0)
    '''
       0   1

    2
    |
    4
    '''
    assert_equal(d.up, {
        0: set(),
        1: set(),
        2: set(),
        4: set([2])
    })
    assert_equal(d.down, {
        0: set(),
        1: set(),
        2: set([4]),
        4: set()
    })


def test_dict():
    d = make()
    d = Dag.from_dict(d.to_dict())
    assert_equal(d.up, {
        0: set(),
        1: set(),
        2: set([0]),
        3: set([0, 1]),
        4: set([0, 1, 2, 3])
    })
    assert_equal(d.down, {
        0: set([2, 3, 4]),
        1: set([3, 4]),
        2: set([4]),
        3: set([4]),
        4: set()
    })
