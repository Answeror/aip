#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
import aip.store
from datetime import datetime


def _field(item):
    if type(item) is tuple:
        k, t = item
    else:
        k = item
        t = unicode

    def inner(t):
        if t is unicode:
            t = ndb.StringProperty
        elif t is int:
            t = ndb.IntegerProperty
        elif t is datetime:
            t = ndb.DateTimeProperty
        elif t is bytes:
            t = lambda: ndb.BlobProperty(indexed=False)
        elif type(t) is unicode and t == u'text':
            t = ndb.TextProperty
        else:
            assert False, 'unknown type: {0}'.format(t)
        return t

    if type(t) is list:
        t = inner(t[0])(repeated=True)
    else:
        t = inner(t)()

    return k, t


def _fields(items):
    return dict([_field(item) for item in items])


Image = type('Image', (aip.store.Image, ndb.Model), _fields(aip.store.IMAGE_FIELDS))
Site = type('Site', (aip.store.Site, ndb.Model), _fields(aip.store.SITE_FIELDS))
Cache = type('Cache', (aip.store.Cache, ndb.Model), _fields(aip.store.CACHE_FIELDS))


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
        if not type(o).query(type(o).id == o.id).iter().has_next():
            o.put()

    def get_images_order_bi_ctime(self, r):
        for i, im in enumerate(Image.query().order(-Image.ctime)):
            if i in r:
                yield im

    def get_site_bi_id(self, id):
        q = Site.query(Site.id == id).iter()
        return q.next() if q.has_next() else None

    def latest_ctime_bi_site_id(self, id):
        q = Image.query(Image.site_id == id).order(-Image.ctime).iter()
        if not q.has_next():
            return None
        return q.next().ctime

    def get_cache_bi_id(self, id):
        q = Cache.query(Cache.id == id).iter()
        return q.next() if q.has_next() else None
