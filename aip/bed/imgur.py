#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
from base64 import b64encode
from collections import namedtuple
from urllib.error import HTTPError
from .base import FetchImageMixin
from ..log import Log
from random import shuffle
import requests


log = Log(__name__)

imgur_thumbnails = (
    ('t', 160, 160),
    ('m', 320, 320),
    ('l', 640, 640),
    ('h', 1024, 1024)
)


Image = namedtuple('Image', ('kind', 'md5', 'id', 'deletehash', 'link'))


class Imgur(FetchImageMixin):

    name = 'imgur'

    def __init__(
        self,
        client_ids,
        timeout,
        album_deletehash,
        resolution_level=1,
        http=None
    ):
        super(Imgur, self).__init__(http=http, timeout=timeout)
        self.client_ids = client_ids
        self.resolution_level = resolution_level
        self.timeout = timeout
        self.album_deletehash = album_deletehash

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

    def shuffled_client_ids(self):
        client_ids = self.client_ids[:]
        shuffle(client_ids)
        return client_ids

    def upload_bi_data(self, data, md5):
        def use_one_client_id(client_id):
            try:
                log.info(
                    'upload {} data to imgur using client_id {}',
                    md5,
                    client_id
                )
                r = requests.post(
                    url='https://api.imgur.com/3/image',
                    headers={'Authorization': 'Client-ID %s' % client_id},
                    data={
                        'image': b64encode(data),
                        'type': 'base64',
                        'title': md5,
                        'album': self.album_deletehash
                    }
                )
                if not r.ok:
                    raise Exception(r.text)

                d = r.json()
                return Image(
                    kind='imgur',
                    md5=md5,
                    id=d['data']['id'],
                    deletehash=d['data']['deletehash'],
                    link=d['data']['link']
                )
            except:
                log.exception(
                    'upload {} data to imgur using client_id {} failed',
                    md5,
                    client_id
                )
                return None

        for client_id in self.shuffled_client_ids():
            ret = use_one_client_id(client_id)
            if ret is not None:
                return ret

    def upload(self, **kargs):
        if 'data' in kargs:
            return self.upload_bi_data(data=kargs['data'], md5=kargs['md5'])
        elif 'url' in kargs:
            return self.upload_bi_url(url=kargs['url'], md5=kargs['md5'])
        else:
            assert False, 'must provide data or url field'

    def upload_bi_url(self, url, md5):

        def use_one_client_id(client_id):
            image_url = url

            def use_file():
                try:
                    log.info('upload file {}', image_url)
                    r = self.call(
                        client_id=client_id,
                        method='POST',
                        url='https://api.imgur.com/3/image',
                        data={
                            'image': b64encode(self.download(image_url)),
                            'type': 'base64',
                            'title': md5,
                            'album': self.album_deletehash
                        }
                    )
                    log.info('upload file {} done', image_url)
                    return r
                except:
                    log.exception('upload file {} failed', image_url)
                    return None

            try:
                log.info('upload link {}', image_url)
                r = self.call(
                    client_id=client_id,
                    method='POST',
                    url='https://api.imgur.com/3/image',
                    data={
                        'image': image_url,
                        'type': 'URL',
                        'title': md5,
                        'album': self.album_deletehash
                    }
                )
                if not r['success']:
                    log.error(
                        'upload link {} failed, response: {}',
                        image_url,
                        r
                    )
                    if r['status'] == 400:
                        r = use_file()
                        if r is None:
                            return None
                    else:
                        return None
                else:
                    log.info('upload link {} done', image_url)
            except:
                log.exception('upload link {} failed', image_url)
                r = use_file()
                if r is None:
                    return None

            data = r['data']
            return Image(
                kind='imgur',
                md5=md5,
                id=data['id'],
                deletehash=data['deletehash'],
                link=data['link']
            )

        def fail():
            raise Exception('upload %s failed' % md5)

        client_ids = self.client_ids[:]
        shuffle(client_ids)
        for client_id in client_ids:
            log.info('use client id {}', client_id)
            ret = use_one_client_id(client_id)
            if ret is not None:
                return ret
            log.info('client id {} failed', client_id)

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
