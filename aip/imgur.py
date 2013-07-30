#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import PIL
import json
import logging
from io import BytesIO
from base64 import b64encode
from collections import namedtuple


imgur_thumbnails = (
    ('t', 160, 160),
    ('m', 320, 320),
    ('l', 640, 640),
    ('h', 1024, 1024)
)


Image = namedtuple('Image', ('md5', 'id', 'deletehash', 'link'))


class Imgur(object):

    def __init__(
        self,
        client_ids,
        resolution_level,
        max_size,
        timeout,
        http
    ):
        self.client_ids = client_ids
        self.resolution_level = resolution_level
        self.max_size = max_size
        self.timeout = timeout
        self.http = http

    def _fetch(self, url):
        return self.http.request('GET', url)

    def _fetch_image(self, url):
        try:
            logging.info('fetch image: %s' % url)
            r = self._fetch(url)
            return r.data
        except Exception as e:
            logging.error('fetch image failed: %s' % url)
            logging.exception(e)
            return None

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

    def upload(self, image):
        from urllib.request import Request, urlopen
        from urllib.parse import urlencode
        from random import shuffle

        def inner(client_id):
            image_url = image.sample_url if image.sample_url else image.image_url

            def deal(r):
                try:
                    logging.error('make_imgur failed with error code %d and message: %s' % (r['status'], r['data']['error']['message']))
                except:
                    logging.error(r)

                logging.info('download and resize')
                if r['status'] == 400:
                    input_stream = BytesIO(self._fetch_image(image_url))
                    image = PIL.Image.open(input_stream)
                    image.thumbnail(
                        self.max_size,
                        PIL.Image.ANTIALIAS
                    )
                    output_stream = BytesIO()
                    image.convert('RGB').save(output_stream, format='JPEG')
                    r = urlopen(Request(
                        'https://api.imgur.com/3/image',
                        headers={'Authorization': 'Client-ID %s' % client_id},
                        data=urlencode({
                            'image': b64encode(output_stream.getvalue()),
                            'type': 'base64'
                        }).encode('ascii')
                    ), timeout=self.timeout).read()
                    return json.loads(r.decode('utf-8'))

            try:
                r = urlopen(Request(
                    'https://api.imgur.com/3/image',
                    headers={'Authorization': 'Client-ID %s' % client_id},
                    data=urlencode({
                        'image': image_url,
                        'type': 'URL'
                    }).encode('ascii')
                ), timeout=self.timeout).read()
                r = json.loads(r.decode('utf-8'))
                if not r['success']:
                    r = deal(r)
                    if r is None:
                        return None
            except Exception as e:
                logging.error('make_imgur failed')
                logging.exception(e)
                try:
                    r = json.loads(e.read().decode('utf-8'))
                    if not r['success']:
                        r = deal(r)
                        if r is None:
                            return None
                except Exception as e:
                    logging.exception(e)
                    return None

            data = r['data']
            return Image(
                md5=image.md5,
                id=data['id'].encode('ascii'),
                deletehash=data['deletehash'].encode('ascii'),
                link=data['link']
            )

        client_ids = self.client_ids[:]
        shuffle(client_ids)
        for client_id in client_ids:
            logging.info('use client id: %s' % client_id)
            ret = inner(client_id)
            if ret is not None:
                return ret
            logging.info('client id %s failed' % client_id)
        return None
