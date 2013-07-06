#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datetime import datetime
from urllib.parse import urljoin
from xml.etree import ElementTree
from . import booru


class Source(booru.Source):

    @property
    def start_page(self):
        return 0

    @property
    def nsfw_tag(self):
        return "rating:safe"

    @property
    def image_url_template(self):
        return urljoin(
            self.url,
            "/index.php?page=dapi&s=post&q=index&tags=%s&limit=%s&pid=%s"
        )

    @property
    def tag_url_template(self):
        return urljoin(
            self.url,
            "/index.php?page=dapi&s=tag&q=index&limit=%s&pid=%s"
        )

    def parse(self, response):
        return ElementTree.XML(response.data.decode('utf-8'))

    @property
    def id(self):
        return 'gelbooru.com'

    @property
    def name(self):
        return 'gelbooru.com'

    @property
    def url(self):
        return 'http://gelbooru.com'

    def image_from_dict(self, d):
        d = d.attrib
        return self.make_image(
            url=urljoin(self.url, d['file_url']),
            width=int(d['width']),
            height=int(d['height']),
            rating=d['rating'],
            score=float(d['score']),
            preview_url=urljoin(self.url, d['preview_url']),
            sample_url=d['sample_url'],
            tags=d['tags'].replace(' ', ';'),
            ctime=datetime.utcfromtimestamp(datetime.strptime(
                d['created_at'],
                '%a %b %d %H:%M:%S %z %Y'
            ).timestamp()),
            mtime=None,
            site_id=self.id,
            post_id=d['id'],
            post_url=urljoin(self.url, '/post/view/{}'.format(d['id']))
        )
