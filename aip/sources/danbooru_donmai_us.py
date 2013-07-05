#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datetime import datetime
from urllib.parse import urljoin
from . import danbooru


class Source(danbooru.Source):

    @property
    def id(self):
        return 'danbooru.donmai.us'

    @property
    def name(self):
        return 'danbooru.donmai.us'

    @property
    def url(self):
        return 'http://danbooru.donmai.us'

    def image_from_dict(self, d):
        return self.make_image(
            url=urljoin(self.url, d['file_url']),
            width=d['width'],
            height=d['height'],
            rating=d['rating'],
            score=d['score'],
            preview_url=urljoin(self.url, d['preview_url']),
            sample_url=None,
            tags=d['tags'].replace(' ', ';'),
            ctime=datetime.strptime(d['created_at'], '%Y-%m-%d %H:%M:%S'),
            mtime=None,
            site_id=self.id,
            post_id=d['id'],
            post_url=urljoin(self.url, '/posts/{}'.format(d['id']))
        )
