#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime
from hashlib import md5
import abc
from .abc import MetaWithFields as StoreMeta


class Meta(object, metaclass=StoreMeta):

    FIELDS = (
        ('id', str, {'length': 128, 'primary_key': True}),
        ('value', bytes)
    )


class User(object, metaclass=StoreMeta):

    FIELDS = (
        ('id', bytes, {'length': 128, 'primary_key': True}),
        ('openid', str),
        ('name', str, {'length': 128}),
        ('email', str, {'length': 256})
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
        'post_url',
        ('md5', bytes, {'length': 128})
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
    def put(self, o):
        return

    def put_user(self, user):
        if user.id is None:
            assert user.openid is not None
            m = md5()
            m.update(user.openid.encode('utf-8'))
            user.id = m.hexdigest().encode('ascii')
        return self.put(user)

    @abc.abstractmethod
    def add_or_update(self, o):
        return

    @abc.abstractmethod
    def put_image(self, im):
        return

    @abc.abstractmethod
    def get_image_bi_md5(self, md5):
        return

    @abc.abstractmethod
    def get_images_order_bi_ctime(self, r):
        return

    @abc.abstractmethod
    def get_unique_images_order_bi_ctime(self, r):
        return

    @abc.abstractmethod
    def latest_ctime_bi_site_id(self, id):
        return

    @abc.abstractmethod
    def image_count(self):
        return

    @abc.abstractmethod
    def user_count(self):
        return

    @abc.abstractmethod
    def unique_image_count(self):
        return

    @abc.abstractmethod
    def set_meta(self, id, value):
        return

    @abc.abstractmethod
    def get_meta(self, id):
        return

    @abc.abstractmethod
    def get_user_bi_id(self, id):
        return

    def get_user_bi_openid(self, openid):
        m = md5()
        m.update(openid.encode('utf-8'))
        return self.get_user_bi_id(m.hexdigest().encode('ascii'))
