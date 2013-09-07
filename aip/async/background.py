#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from multiprocessing import Pool, cpu_count
from functools import partial, wraps
from ..fn import F


class Background(object):

    def __init__(self, slave_count=None):
        self.slave_count = cpu_count() if slave_count is None else slave_count

    def start(self):
        self.slaves = Pool(processes=min(cpu_count(), self.slave_count))

    def stop(self):
        self.slaves.join()

    def action(self, job, rank=0):
        self.slaves.apply_async(job)

    def function(self, job, callback, rank=0):
        return self.action(F(callback) << job, rank=rank)
