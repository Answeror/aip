#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import abc
from ..abc import MetaWithFields
import urllib3


_http = urllib3.PoolManager()


class Source(object, metaclass=MetaWithFields):

    FIELDS = ('id', 'name', 'has_ssl')

    def __init__(self, make_post):
        self.make_post = make_post

    @abc.abstractmethod
    def get_images(self, tags, page=None, per=None):
        return

    @property
    def http(self):
        return self._http if hasattr(self, '_http') else _http

    def contains(self, uri):
        return self.name in uri

    def try_use_ssl(self, uri):
        assert self.contains(uri)
        return uri.replace('http://', 'https://') if self.has_ssl else uri
