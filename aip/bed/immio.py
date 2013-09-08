#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import logging
from base64 import b64encode
from collections import namedtuple
from urllib.error import HTTPError
from .base import FetchImageMixin


Image = namedtuple('Image', ('md5', 'uid', 'uri', 'width', 'height'))


class Immio(FetchImageMixin):

    name = 'immio'

    def __init__(
        self,
        max_size,
        timeout,
        http=None
    ):
        super(Immio, self).__init__(http=http, timeout=timeout)
        self.max_size = max_size
        self.timeout = timeout

    def call(self, md5, data):
        try:
            r = self.http.request(
                method='POST',
                url='http://imm.io/store/',
                fields={
                    'image': b'data:image/jpeg;base64,' + b64encode(data),
                    'name': md5
                },
                timeout=self.timeout,
                retries=0
            )
            return json.loads(r.data.decode('utf-8'))
        except HTTPError as e:
            return json.loads(e.read().decode('utf-8'))

    def upload(self, url, md5):
        def fail():
            raise Exception('upload %s failed' % md5)

        try:
            r = self.call(md5, self.download(url))
        except Exception as e:
            logging.exception(e)
            fail()

        if not r['success']:
            logging.error('upload failed, response: {}'.format(r))
            fail()

        data = r['payload']
        return Image(
            md5=md5,
            uid=data['uid'],
            uri=data['uri'],
            width=int(data['width']),
            height=int(data['height'])
        )
