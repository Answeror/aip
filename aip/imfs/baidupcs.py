from .base import NameMixin, ImfsError, NotFoundError, guarded
from .utils import thumbnail
from pprint import pformat
from .. import img
from datetime import datetime


BASE = '/apps/aip/cache/'


class PCSError(ImfsError):
    pass


class BadResponse(PCSError):

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


def error_code(r):
    try:
        d = r.json()
        code = d.get('error_code', None)
        if code is None:
            code = d.get('content', {}).get('error_code', None)
        return code
    except:
        return None


class BaiduPCS(NameMixin):

    def __init__(self, access_token):
        self.access_token = access_token

    @guarded
    def _load(self, name):
        r = self.pcs.download(wrap(name))
        if r.status_code == 404:
            return None
        if not r.ok:
            raise BadResponse(r)
        return r.content

    @guarded
    def _save(self, name, data):
        r = self.pcs.upload(wrap(name), data, ondup='overwrite')
        if not r.ok:
            if r.status_code == 400 and error_code(r) == 31061:
                pass
            else:
                raise BadResponse(r)

    def _thumbnail(self, name, width, height):
        data = self.load(name)
        if data is None:
            return None
        kind = img.kind(data=data)
        if kind is None:
            raise PCSError('cannot detect image type')
        return thumbnail(data, kind, width, height)

    @guarded
    def _has(self, name):
        r = self.pcs.meta(wrap(name))
        if r.status_code == 404:
            return False
        if not r.ok:
            raise BadResponse(r)
        return True

    @guarded
    def _remove(self, name):
        r = self.pcs.delete(wrap(name))
        if not r.ok and r.status_code not in (404,):
            raise BadResponse(r)

    @guarded
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


@guarded
def ensure_base(pcs, base):
    r = pcs.mkdir(base)
    if not r.ok:
        if r.status_code == 400 and error_code(r) == 31061:
            r = pcs.meta(base)
            if not r.ok:
                raise BadResponse(r)
            if not r.json()['list'][0]['isdir']:
                raise PCSError('%s is not dir' % base)
        else:
            raise BadResponse(r)
