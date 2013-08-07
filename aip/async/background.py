#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from queue import Queue
from threading import Thread
from functools import wraps, partial


class Background(object):

    def __init__(self, slave_count=1):
        self.slave_count = slave_count
        self.slaves = []
        self.jobs = Queue()

    def start(self):
        for i in range(self.slave_count):
            t = Thread(target=self._run, daemon=True)
            t.start()
            self.slaves.append(t)

    def stop(self):
        self.jobs.join()

    def _run(self):
        while True:
            job = self.jobs.get()
            try:
                job()
            except Exception as e:
                logging.exception(e)
            finally:
                self.jobs.task_done()

    def action(self, job):
        self.jobs.put(job)

    def function(self, job, callback):
        @wraps(job)
        def inner():
            self.action(partial(callback, job()))
        return self.action(inner)
