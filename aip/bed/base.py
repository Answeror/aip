#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import PIL.Image
import logging
from io import BytesIO
import urllib3


_http = urllib3.PoolManager()


class FetchImageMixin(object):

    def __init__(
        self,
        timeout,
        http=None
    ):
        self.timeout = timeout
        if http:
            self._http = http

    @property
    def http(self):
        return self._http if hasattr(self, '_http') else _http

    def _fetch_image(self, url):
        r = self.http.request(
            method='GET',
            url=url,
            timeout=self.timeout,
            retries=0
        )
        return r.data

    def download(self, uri):
        logging.info('download %s' % uri)
        try:
            input_stream = BytesIO(self._fetch_image(uri))
            pim = PIL.Image.open(input_stream)
            pim.thumbnail(
                self.max_size,
                PIL.Image.ANTIALIAS
            )
            output_stream = BytesIO()
            pim.convert('RGB').save(output_stream, format='JPEG')
            value = output_stream.getvalue()
            logging.info('download %s done' % uri)
            return value
        except Exception as e:
            logging.exception(e)
            raise Exception('download %s failed' % uri)
