#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from collections import deque
from datetime import datetime, timedelta
from functools import wraps
import threading


class EventQueue(object):

    def __init__(self, maxlen):
        self.q = deque(maxlen=maxlen)
        self.lock = threading.RLock()

    def locked(f):
        @wraps(f)
        def inner(self, *args, **kargs):
            with self.lock:
                return f(self, *args, **kargs)
        return inner

    @locked
    def push(self, value):
        self.q.append((datetime.utcnow(), value))

    @locked
    def pop(self, **kargs):
        interval = timedelta(**kargs)
        start = datetime.utcnow() - interval
        buf = []
        for time, value in reversed(self.q):
            if start <= time:
                buf.append(value)
            else:
                break
        return list(reversed(buf))
