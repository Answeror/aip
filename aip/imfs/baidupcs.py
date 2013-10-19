from .base import NameMixin
from .utils import thumbnail
from pprint import pformat
import imghdr


BASE = '/apps/aip/'


class PCSException(Exception):
    pass


class BadResponse(PCSException):

    def __init__(self, r):
        self.status_code = r.status_code
        try:
            self.content = r.json()
        except:
            self.content = r.content

    def __str__(self):
        return pformat({
            'status_code': self.status_code,
            'content': self.content
        })


def wrap(name):
    return BASE + name


class BaiduPCS(NameMixin):

    def __init__(self, access_token):
        self.access_token = access_token

    def _load(self, name):
        r = self.pcs.download(wrap(name))
        if not r.ok:
            raise BadResponse(r)
        return r.content

    def _save(self, name, data):
        r = self.pcs.upload(wrap(name), data, ondup='overwrite')
        if not r.ok:
            raise BadResponse(r)

    def _thumbnail(self, name, width, height):
        data = self.load(name)
        kind = imghdr.what('foo', data)
        if kind is None:
            raise PCSException('cannot detect image type')
        return thumbnail(data, kind, width, height)

    def _has(self, name):
        r = self.pcs.meta(wrap(name))
        if r.status_code == 404:
            return False
        if not r.ok:
            raise BadResponse(r)
        return True

    def _remove(self, name):
        r = self.pcs.delete(wrap(name))
        if not r.ok and r.status_code not in (404,):
            raise BadResponse(r)

    @property
    def pcs(self):
        if not hasattr(self, '_pcs'):
            from baidupcs import PCS
            self._pcs = PCS(self.access_token)
        return self._pcs
