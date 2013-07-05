#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import flask
import threading
import logging
import pickle
from datetime import datetime


def _ensure_exists(path):
    assert os.path.exists(path), 'file not exist: %s' % path


class Blueprint(flask.Blueprint):

    lock = threading.RLock()

    def locked(f):
        def inner(self, *args, **kargs):
            with Blueprint.lock:
                return f(self, *args, **kargs)
        return inner

    def __init__(self, *args, **kargs):
        super(Blueprint, self).__init__(*args, **kargs)

    def local(self):
        from .local import Local
        return Local(self)

    @property
    def store(self):
        if not hasattr(self, '_store'):
            from . import store_impl
            self._store = store_impl
        return self._store

    @store.setter
    def store(self, value):
        self._store = value

    @property
    @locked
    def sources(self):
        if not hasattr(self, '_sources'):
            self._sources = []
            import pkgutil
            import importlib
            from inspect import isabstract
            from . import sources
            for _, name, _ in list(pkgutil.iter_modules([os.path.dirname(sources.__file__)])):
                module = importlib.import_module('.sources.' + name, 'aip')
                if hasattr(module, 'Source'):
                    source = getattr(module, 'Source')
                    if not isabstract(source):
                        self._sources.append(source)
        return self._sources

    @locked
    def update(self, begin=None):
        self.last_update_time = datetime.now()
        self.update_images(begin)

    @property
    def last_update_time(self):
        with self.connection() as con:
            value = con.get_meta('last_update_time')
            return None if value is None else pickle.loads(value)

    @last_update_time.setter
    def last_update_time(self, value):
        with self.connection() as con:
            con.set_meta('last_update_time', pickle.dumps(value))
            con.commit()

    @property
    @locked
    def repo(self):
        if not hasattr(self, '_repo'):
            self._repo = self.store.Repo()
        return self._repo

    @locked
    def update_images(self, begin=None, limit=65536):
        with self.connection() as con:
            for make in self.sources:
                source = make(self.store.Image)
                latest_ctime = con.latest_ctime_bi_site_id(source.id)
                tags = []
                for i, im in zip(list(range(limit)), source.get_images(tags)):
                    if begin is not None and im.ctime <= begin:
                        break
                    if latest_ctime is not None and im.ctime <= latest_ctime:
                        break
                    con.add_or_update(im)
                con.commit()

    def connection(self):
        return self.repo.connection()
