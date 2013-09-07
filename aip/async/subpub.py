#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from multiprocessing import Manager, Queue, RLock
from queue import Empty


manager = Manager()


class Subpub(object):

    def __init__(self):
        self.qs = {}
        self.lock = manager.RLock()

    def push(self, key, value):
        with self.lock:
            if key not in self.qs:
                self.qs[key] = manager.Queue()
            q = self.qs[key]
        q.put(value)

    def pop(self, key, timeout=None):
        try:
            with self.lock:
                if key not in self.qs:
                    self.qs[key] = manager.Queue()
                q = self.qs[key]
            return q.get(timeout=timeout) if timeout else q.get()
        except Empty:
            raise Exception('timeout')

    def kill(self, key):
        with self.lock:
            if key in self.qs:
                del self.qs[key]
