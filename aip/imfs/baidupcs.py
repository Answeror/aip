from .base import NameMixin, ImfsError, NotFoundError
from .utils import thumbnail
from pprint import pformat
from .. import img
from datetime import datetime


BASE = '/apps/aip/cache/'


class PCSException(ImfsError):
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
        if r.status_code == 404:
            return None
        if not r.ok:
            raise BadResponse(r)
        return r.content

    def _save(self, name, data):
        r = self.pcs.upload(wrap(name), data, ondup='overwrite')
        if not r.ok:
            raise BadResponse(r)

    def _thumbnail(self, name, width, height):
        data = self.load(name)
        if data is None:
            return None
        kind = img.kind(data=data)
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

    def _mtime(self, name):
        r = self.pcs.meta(wrap(name))
        if not r.ok:
            if r.status_code == 404:
                raise NotFoundError(name)
            raise BadResponse(r)
        return datetime.fromtimestamp(r.json()['list'][0]['mtime'])

    def _cache_timeout(self, name):
        return None

    @property
    def pcs(self):
        if not hasattr(self, '_pcs'):
            from baidupcs import PCS
            self._pcs = PCS(self.access_token)
            ensure_base(self._pcs, BASE)
        return self._pcs


def ensure_base(pcs, base):
    r = pcs.mkdir(base)
    if not r.ok:
        if r.status_code == 400 and r.json()['error_code'] == 31061:
            r = pcs.meta(base)
            if not r.ok:
                raise BadResponse(r)
            if not r.json()['list'][0]['isdir']:
                raise PCSException('%s is not dir' % base)
        else:
            raise BadResponse(r)
