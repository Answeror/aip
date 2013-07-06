#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import abc
import logging
from ..abc import MetaWithFields
from . import base


LIMIT_MIN = 128


class Source(base.Source, metaclass=MetaWithFields):

    FIELDS = ('url', 'start_page', 'nsfw_tag')

    def __init__(self, make_image):
        super(Source, self).__init__(make_image)
        import urllib3
        self._http = urllib3.PoolManager()

    @property
    def filter_nsfw(self):
        return True

    def _fetch(self, request_url):
        try:
            return self._http.request('GET', request_url)
        except Exception as e:
            logging.info('fetch failed: %s' % request_url)
            logging.exception(e)
            return None

    def _get(self, request_url):
        r = self._fetch(request_url)
        return self.parse(r) if r is not None else []

    @abc.abstractmethod
    def parse(self, response):
        return

    @abc.abstractmethod
    def image_from_dict(self, d):
        return

    def _request_images(self, tags):
        limit = LIMIT_MIN
        page = self.start_page
        end = False
        fetched = 0
        while not end:
            logging.debug('limit %d' % limit)
            page_link = self.image_url_template % ('+'.join(tags), limit, page)
            images = list(self._get(page_link))
            if len(images) < limit:
                end = True
            for im in images[fetched:]:
                yield im
            fetched = len(images)
            # doubling next fetch
            limit += limit

    def _request_paged_images(self, tags, page, per):
        page = self.start_page + page
        page_link = self.image_url_template % ('+'.join(tags), per, page)
        for im in self._get(page_link):
            yield im

    def get_images(self, tags, page=None, per=None):
        if self.filter_nsfw:
            tags.append(self.nsfw_tag)

        if page is None or per is None:
            images = self._request_images(tags)
        else:
            images = self._request_paged_images(tags, page, per)

        for im in images:
            yield self.image_from_dict(im)

    def get_tags(self):
        for tags in self._request_tag():
            for tag in tags:
                yield tag.count, tag.name

    def _request_tag(self):
        limit = 100
        page = self.start_page
        end = False
        while not end:
            page_link = self.tag_url_template % (limit, page)
            tags = self._get(page_link)
            if len(tags) < limit:
                end = True
            yield tags
            page += 1
