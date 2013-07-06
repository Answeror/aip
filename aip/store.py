#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime
import abc
from .abc import MetaWithFields as StoreMeta


class Meta(object, metaclass=StoreMeta):

    FIELDS = (
        ('id', str, {'length': 128, 'primary_key': True}),
        ('value', bytes)
    )


class Image(object, metaclass=StoreMeta):

    FIELDS = (
        ('id', str, {'length': 128, 'primary_key': True}),
        'url',
        ('width', int),
        ('height', int),
        'rating',
        ('score', float),
        'preview_url',
        'sample_url',
        'tags',
        ('ctime', datetime),
        ('mtime', datetime),
        ('site_id', str, {'length': 128}),
        ('post_id', int),
        'post_url'
    )


class Repo(object, metaclass=StoreMeta):

    @abc.abstractmethod
    def connection(self):
        return

    @abc.abstractmethod
    def clear(self):
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
    def put_image(self, im):
        return

    @abc.abstractmethod
    def get_images_order_bi_ctime(self, r):
        return

    @abc.abstractmethod
    def latest_ctime_bi_site_id(self, id):
        return

    @abc.abstractmethod
    def image_count(self):
        return

    @abc.abstractmethod
    def set_meta(self, id, value):
        return

    @abc.abstractmethod
    def get_meta(self, id):
        return
