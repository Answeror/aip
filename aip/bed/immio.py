#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import PIL
import json
import logging
from io import BytesIO
from base64 import b64encode
from collections import namedtuple
from urllib.error import HTTPError


Image = namedtuple('Image', ('md5', 'uid', 'uri', 'width', 'height'))


class Immio(object):

    def __init__(
        self,
        max_size,
        timeout,
        http
    ):
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

    def call(self, md5, data):
        try:
            r = self.http.request(
                method='POST',
                url='http://imm.io/store/',
                fields={
                    'image': b'data:image/png;base64,' + b64encode(data),
                    'name': md5
                },
                timeout=self.timeout
            )
            return json.loads(r.data.decode('utf-8'))
        except HTTPError as e:
            return json.loads(e.read().decode('utf-8'))

    def upload(self, image):
        def download(uri):
            input_stream = BytesIO(self._fetch_image(uri))
            pim = PIL.Image.open(input_stream)
            pim.thumbnail(
                self.max_size,
                PIL.Image.ANTIALIAS
            )
            output_stream = BytesIO()
            pim.convert('RGB').save(output_stream, format='JPEG')
            return output_stream.getvalue()

        r = self.call(image.md5, download(image.sample_url if image.sample_url else image.image_url))

        if not r['success']:
            return None

        data = r['payload']
        return Image(
            md5=image.md5,
            uid=data['uid'].encode('ascii'),
            uri=data['uri'],
            width=int(data['width']),
            height=int(data['height'])
        )
