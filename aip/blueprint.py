#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import flask
import threading
import pickle
from datetime import datetime
from functools import wraps
from flask import request


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
        self.temp_path = kargs['temp_path']
        del kargs['temp_path']
        self.oid = kargs['oid']
        del kargs['oid']
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
                tags = []
                for i, im in zip(list(range(limit)), source.get_images(tags)):
                    if begin is not None and im.ctime <= begin:
                        break
                    con.put_image(im)
                con.commit()

    @property
    def sample_width(self):
        from .settings import SAMPLE_WIDTH
        return SAMPLE_WIDTH

    def connection(self):
        return self.repo.connection()

    @locked
    def clear(self):
        self.repo.clear()

    @property
    @locked
    def cache(self):
        if not hasattr(self, '_cache'):
            from .cache import SqliteCache
            self._cache = SqliteCache(os.path.join(self.temp_path, 'cache'))
        return self._cache

    def cached(self, timeout=5 * 60, key='view/%s'):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                cache_key = key % request.path
                rv = self.cache.get(cache_key)
                if rv is not None:
                    return rv
                rv = f(*args, **kwargs)
                self.cache.set(cache_key, rv, timeout=timeout)
                return rv
            return decorated_function
        return decorator
