#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import flask
import threading
import logging
import pickle
from datetime import datetime
from .settings import PROVIER_CONFIG_FILE_FILENAME


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

    @locked
    def config(self, path):
        _ensure_exists(path)
        self._manager = self._make_manager(path)

    def _make_manager(self, path):
        _ensure_exists(path)
        from BooruPy import BooruManager
        return BooruManager.from_python_file(path)

    @property
    @locked
    def manager(self):
        if not hasattr(self, '_manager'):
            self._manager = self._make_manager(os.path.join(
                self.static_folder,
                PROVIER_CONFIG_FILE_FILENAME
            ))
        return self._manager

    @property
    @locked
    def providers(self):
        return self.manager.providers

    @locked
    def update(self, begin=None):
        self.last_update_time = datetime.now()
        self.update_sites()
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
    def update_sites(self):
        with self.connection() as con:
            for p in self.providers:
                site = self.store.Site(
                    id=p.shortname,
                    name=p.name,
                    url=p._base_url
                )
                logging.debug('update site: %s' % site.name)
                con.add_or_update(site)
            con.commit()

    @locked
    def update_images(self, begin=None, limit=65536):
        with self.connection() as con:
            for p in self.providers:
                site = con.get_site_bi_id(p.shortname)
                if site is not None:
                    latest_ctime = con.latest_ctime_bi_site_id(site.id)
                    tags = []
                    for i, im in zip(list(range(limit)), p.get_images(tags)):
                        im = self._make_image(im, site.id)
                        if begin is not None and im.ctime <= begin:
                            break
                        if latest_ctime is not None and im.ctime <= latest_ctime:
                            break
                        con.add_or_update(im)
                con.commit()

    def _make_image(self, source, site_id):
        return self.store.Image(
            id=None,
            url=source.url,
            width=source.width,
            height=source.height,
            rating=source.rating,
            score=source.score,
            preview_url=source.preview_url,
            sample_url=source.sample_url if hasattr(source, 'sample_url') else None,
            tags=source.tags,
            ctime=source.ctime,
            mtime=source.mtime if hasattr(source, 'mtime') else None,
            site_id=site_id
        )

    def connection(self):
        return self.repo.connection()
