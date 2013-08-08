#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from functools import wraps
from queue import Queue, Empty
import threading


class Subpub(object):

    def __init__(self):
        self.qs = {}
        self.lock = threading.RLock()

    def locked(f):
        @wraps(f)
        def inner(self, *args, **kargs):
            with self.lock:
                return f(self, *args, **kargs)
        return inner

    def push(self, key, value):
        with self.lock:
            if key not in self.qs:
                self.qs[key] = Queue()
            q = self.qs[key]
        q.put(value)

    def pop(self, key, timeout=None):
        try:
            with self.lock:
                if key not in self.qs:
                    self.qs[key] = Queue()
                q = self.qs[key]
            return q.get(timeout=timeout) if timeout else q.get()
        except Empty:
            raise Exception('timeout')

    @locked
    def kill(self, key):
        if key in self.qs:
            del self.qs[key]
