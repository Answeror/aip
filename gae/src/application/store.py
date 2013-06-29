#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
import aip.store
from datetime import datetime


def _add_property(cls, item):
    if type(item) is tuple:
        k, t = item
    else:
        k = item
        t = str
    if t is str:
        t = ndb.StringProperty
    elif t is int:
        t = ndb.IntegerProperty
    elif t is datetime:
        t = ndb.DateTimeProperty
    elif t is bytes:
        t = ndb.BlobProperty
    else:
        assert False, 'unknown type: {0}'.format(t)
    setattr(cls, k, t())


class Image(aip.store.Image, ndb.Model):
    pass


for item in aip.store.IMAGE_FIELDS:
    _add_property(Image, item)


class Site(aip.store.Site, ndb.Model):
    pass


for item in aip.store.SITE_FIELDS:
    _add_property(Site, item)


class Cache(aip.store.Cache, ndb.Model):
    pass


for item in aip.store.CACHE_FIELDS:
    _add_property(Cache, item)


class Repo(aip.store.Repo):

    def connection(self):
        return Connection()


def _random_name():
    import uuid
    return uuid.uuid4()


class Connection(aip.store.Connection):

    def __init__(self):
        pass

    def __enter__(self, *args, **kargs):
        return self

    def __exit__(self, *args, **kargs):
        pass

    def commit(self):
        pass

    def add_or_update(self, o):
        o.put()

    def get_images_order_bi_ctime(self, r):
        for i, im in enumerate(Image.query().order(-Image.ctime)):
            if i in r:
                yield im

    def get_site_bi_id(self, id):
        q = Site.query(Site.id == id)
        return q.next() if q.has_next() else None

    def latest_ctime_bi_site_id(self, id):
        q = Image.query(Image.site_id == id).order(-Image.ctime)
        if not q.has_next():
            return None
        return q.next().ctime

    def get_cache_bi_id(self, id):
        q = Cache.query(Cache.id == id)
        return q.next() if q.has_next() else None
