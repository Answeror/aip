#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from queue import PriorityQueue
from threading import Thread
from functools import wraps, partial
from datetime import datetime


class Background(object):

    def __init__(self, slave_count=1):
        self.slave_count = slave_count
        self.slaves = []
        self.jobs = PriorityQueue()

    def start(self):
        for i in range(self.slave_count):
            t = Thread(target=self._run, daemon=True)
            t.start()
            self.slaves.append(t)

    def stop(self):
        self.jobs.join()

    def _run(self):
        while True:
            job = self.jobs.get()[2]
            try:
                job()
            except Exception as e:
                logging.exception(e)
            finally:
                self.jobs.task_done()

    def action(self, job, rank=0):
        self.jobs.put((rank, datetime.utcnow(), job))

    def function(self, job, callback, rank=0):
        @wraps(job)
        def inner():
            self.action(partial(callback, job()), rank=rank)
        return self.action(inner, rank=rank)
