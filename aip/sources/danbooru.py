#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
from datetime import datetime
from urllib.parse import urljoin
from . import booru


class Source(booru.Source):

    @property
    def start_page(self):
        return 1

    @property
    def nsfw_tag(self):
        return "rating:s"

    @property
    def image_url_template(self):
        return urljoin(
            self.url,
            "/post/index.json?tags=%s&limit=%s&page=%s"
        )

    @property
    def tag_url_template(self):
        return urljoin(
            self.url,
            "/tags/index.json?limit=%s&page=%s"
        )

    def parse(self, response):
        return json.loads(response.data.decode('utf-8'))

    def image_from_dict(self, d):
        return self.make_image(
            url=urljoin(self.url, d['file_url']),
            width=int(d['width']),
            height=int(d['height']),
            rating=d['rating'],
            score=float(d['score']),
            preview_url=urljoin(self.url, d['preview_url']),
            sample_url=d['sample_url'],
            tags=d['tags'].replace(' ', ';'),
            ctime=datetime.utcfromtimestamp(int(d['created_at'])),
            mtime=None,
            site_id=self.id,
            post_id=d['id'],
            post_url=urljoin(self.url, '/post/view/{}'.format(d['id']))
        )
