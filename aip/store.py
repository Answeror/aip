#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime
import abc


class StoreMeta(abc.ABCMeta):

    def __new__(meta, name, bases, attr):
        if 'FIELDS' in attr:
            fields = attr['FIELDS']
            for field in fields:
                if type(field) is tuple:
                    field, _ = field
                attr[field] = abc.abstractproperty(lambda self: None)
        return abc.ABCMeta.__new__(meta, name, bases, attr)


class Image(object, metaclass=StoreMeta):

    FIELDS = (
        'id',
        'url',
        ('width', int),
        ('height', int),
        'rating',
        ('score', int),
        'preview_url',
        'sample_url',
        ('tags', 'text'),
        ('ctime', datetime),
        ('mtime', datetime),
        'site_id'
    )


class Site(object, metaclass=StoreMeta):

    FIELDS = (
        'id',
        'name',
        'url'
    )


class Cache(object, metaclass=StoreMeta):

    FIELDS = (
        'id',
        ('data', bytes),
        ('meta', bytes)
    )


class Repo(object, metaclass=StoreMeta):

    @abc.abstractmethod
    def connection(self):
        return


class Connection(object, metaclass=StoreMeta):

    @abc.abstractmethod
    def __enter__(self, *args, **kargs):
        return

    @abc.abstractmethod
    def __exit__(self, *args, **kargs):
        return

    @abc.abstractmethod
    def commit(self):
        return

    @abc.abstractmethod
    def add_or_update(self, o):
        return

    @abc.abstractmethod
    def get_images_order_bi_ctime(self, r):
        return

    @abc.abstractmethod
    def get_site_bi_id(self):
        return

    @abc.abstractmethod
    def latest_ctime_bi_site_id(self, id):
        return

    @abc.abstractmethod
    def get_cache_bi_id(self, id):
        return

    @abc.abstractmethod
    def site_count(self):
        return

    @abc.abstractmethod
    def image_count(self):
        return
