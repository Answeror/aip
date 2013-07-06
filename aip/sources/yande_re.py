#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datetime import datetime
from urllib.parse import urljoin
from . import danbooru


class Source(danbooru.Source):

    def __init__(self, make_image):
        super(Source, self).__init__(make_image)

    @property
    def id(self):
        return 'yande.re'

    @property
    def name(self):
        return 'yande.re'

    @property
    def url(self):
        return 'https://yande.re'

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
