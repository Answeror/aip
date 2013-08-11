#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datetime import datetime
from urllib.parse import urljoin
from . import danbooru


class Source(danbooru.Source):

    def image_from_dict(self, d):
        return self.make_post(
            image_url=urljoin(self.url, d['file_url']),
            width=int(d['width']),
            height=int(d['height']),
            rating=d['rating'],
            score=float(d['score']),
            preview_url=urljoin(self.url, d['preview_url']),
            sample_url=None,
            tags=d['tags'].split(' '),
            ctime=datetime.strptime(d['created_at'], '%Y-%m-%d %H:%M:%S'),
            mtime=None,
            site_id=self.id,
            post_id=d['id'],
            post_url=urljoin(self.url, '/posts/{}'.format(d['id'])),
            md5=d['md5']
        )
