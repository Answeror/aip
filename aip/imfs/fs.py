import os
from .base import NameMixin
from .error import ImfsError, NotFoundError
import glob
from .. import img
from .utils import thumbnail
from time import time as now
from datetime import datetime


def ensure_root(root):
    if root is None:
        import tempfile
        root = os.path.join(tempfile.gettempdir(), __name__)
    if not os.path.exists(root):
        os.makedirs(root)
    return root


def touch(fname, times=None):
    os.utime(fname, times)


def sorted_ls(path):
    atime = lambda f: os.path.getatime(os.path.join(path, f))
    return list(sorted(os.listdir(path), key=atime))


class FS(NameMixin):

    def __init__(self, life=30 * 24 * 3600, root=None):
        self.root = ensure_root(root)
        self.life = life
        self.last_clear_time = now()

    def _path(self, name):
        if name.startswith(self.root):
            return name
        return os.path.join(self.root, name)

    def _thumbpath(self, name, width, height):
        assert not name.startswith(self.root)
        return os.path.join(
            self.root,
            '%s.%dx%d' % (name, int(width), int(height))
        )

    def _too_old(self, name):
        return self._elapsed(name) > self.life

    def _elapsed(self, name):
        return now() - os.path.getatime(self._path(name))

    def _from_cache(self, name):
        try:
            path = self._path(name)
            touch(path)
            with open(path, 'rb') as f:
                return f.read()
        except:
            pass

    def _clear_cache(self):
        for path in os.listdir(self.root):
            if self._too_old(path):
                try:
                    os.unlink(path)
                except:
                    pass
        self.last_clear_time = now()

    def _to_cache(self, name, data):
        assert data is not None
        try:
            path = self._path(name)
            with open(path, 'wb') as f:
                f.write(data)
            if now() - self.last_clear_time > self.life:
                self._clear_cache()
        except:
            pass

    def _load(self, name):
        return self._from_cache(name)

    def _save(self, name, data):
        assert data is not None
        self._to_cache(name, data)

    def _thumbnail(self, name, width, height):
        path = self._thumbpath(name, width, height)
        data = self._from_cache(path)
        if data is None:
            data = self.load(name)
            if data is not None:
                kind = img.kind(data=data)
                if kind is None:
                    raise ImfsError('cannot detect image type')
                data = thumbnail(data, kind, width, height)
                self._to_cache(path, data)
        return data

    def _has(self, name):
        return os.path.exists(self._path(name))

    def _remove(self, name):
        for path in glob.glob(self._path(name) + '*'):
            try:
                os.unlink(path)
            except:
                pass

    def _mtime(self, name):
        if not self.has(name):
            raise NotFoundError(name)
        return datetime.fromtimestamp(os.path.getmtime(self._path(name)))

    def _cache_timeout(self, name):
        return self.life
