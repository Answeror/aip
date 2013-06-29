#!/usr/bin/env python
# -*- coding: utf-8 -*-


IMAGE_FIELDS = (
    'id',
    'url',
    'width',
    'height',
    'rating',
    'score',
    'preview_url',
    'sample_url',
    'tags',
    'ctime',
    'mtime',
    'site_id'
)
SITE_FIELDS = (
    'id',
    'name',
    'url'
)


def noimpl(name):
    raise NotImplementedError("%s not implemented" % name)


class Image(object):
    pass


#for field in IMAGE_FIELDS:
    #setattr(Image, field, property(lambda self: noimpl(field)))


class Site(object):
    pass


#for field in SITE_FIELDS:
    #setattr(Image, field, property(lambda self: noimpl(field)))


class Cache(object):
    pass


class Repo(object):

    def connection(self):
        noimpl('connection')


class Connection(object):

    def __enter__(self, *args, **kargs):
        noimpl()

    def __exit__(self, *args, **kargs):
        noimpl()

    def commit(self):
        noimpl('commit')

    def add_or_update(self, o):
        noimpl('add_or_update')

    def get_images_order_bi_ctime(self, r):
        noimpl('get_images_order_bi_ctime')

    def get_site_bi_id(self):
        noimpl('get_site_bi_id')

    def latest_ctime_bi_site_id(self, id):
        noimpl('latest_ctime_bi_site_id')

    def get_cache_bi_id(self, id):
        noimpl('get_cache_bi_id')
