#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import logging
from base64 import b64encode
from collections import namedtuple
from urllib.error import HTTPError
from .base import FetchImageMixin


imgur_thumbnails = (
    ('t', 160, 160),
    ('m', 320, 320),
    ('l', 640, 640),
    ('h', 1024, 1024)
)


Image = namedtuple('Image', ('md5', 'id', 'deletehash', 'link'))


class Imgur(FetchImageMixin):

    def __init__(
        self,
        client_ids,
        resolution_level,
        max_size,
        timeout,
        album_deletehash,
        http
    ):
        super(Imgur, self).__init__(http=http, timeout=timeout)
        self.client_ids = client_ids
        self.resolution_level = resolution_level
        self.max_size = max_size
        self.timeout = timeout
        self.album_deletehash = album_deletehash
        self.http = http

    def call(self, client_id, method, url, data):
        try:
            r = self.http.request(
                method=method,
                url=url,
                fields=data,
                headers={'Authorization': 'Client-ID %s' % client_id},
                timeout=self.timeout,
                retries=0
            )
            return json.loads(r.data.decode('utf-8'))
        except HTTPError as e:
            return json.loads(e.read().decode('utf-8'))

    def upload(self, image):
        from random import shuffle

        def use_one_client_id(client_id):
            image_url = image.sample_url if image.sample_url else image.image_url

            def use_file():
                try:
                    logging.info('upload file %s' % image_url)
                    r = self.call(
                        client_id=client_id,
                        method='POST',
                        url='https://api.imgur.com/3/image',
                        data={
                            'image': b64encode(self.download(image_url)),
                            'type': 'base64',
                            'title': image.md5,
                            'album': self.album_deletehash
                        }
                    )
                    logging.info('upload file %s done' % image_url)
                    return r
                except Exception as e:
                    logging.error('upload file %s failed' % image_url)
                    logging.exception(e)
                    return None

            try:
                logging.info('upload link %s' % image_url)
                r = self.call(
                    client_id=client_id,
                    method='POST',
                    url='https://api.imgur.com/3/image',
                    data={
                        'image': image_url,
                        'type': 'URL',
                        'title': image.md5,
                        'album': self.album_deletehash
                    }
                )
                if not r['success']:
                    logging.error('upload link {} failed, response: {}'.format(image_url, r))
                    if r['status'] == 400:
                        r = use_file()
                        if r is None:
                            return None
                    else:
                        return None
                else:
                    logging.info('upload link %s done' % image_url)
            except Exception as e:
                logging.error('upload link %s failed' % image_url)
                logging.exception(e)
                r = use_file()
                if r is None:
                    return None

            data = r['data']
            return Image(
                md5=image.md5,
                id=data['id'],
                deletehash=data['deletehash'],
                link=data['link']
            )

        def fail():
            raise Exception('upload %s failed' % image.md5)

        client_ids = self.client_ids[:]
        shuffle(client_ids)
        for client_id in client_ids:
            logging.info('use client id %s' % client_id)
            ret = use_one_client_id(client_id)
            if ret is not None:
                return ret
            logging.info('client id %s failed' % client_id)

        fail()

    def best_link(self, image, width, height):
        area = width * height
        ratio = width / height
        for suffix, width, height in imgur_thumbnails:
            if ratio < width / height:
                width = ratio * height
            if area <= self.resolution_level * width * height:
                parts = image.link.split('.')
                assert len(parts) > 1
                parts[-2] = parts[-2] + suffix
                return '.'.join(parts)
        return image.link
