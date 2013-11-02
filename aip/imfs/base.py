import string
import hashlib
from nose.tools import assert_is


def ismd5(s):
    return len(s) == 32 and all(c in string.hexdigits for c in s)


def wrap(name):
    return name if ismd5(name) else tomd5(name)


def tomd5(s):
    assert_is(type(s), str)
    m = hashlib.md5()
    m.update(s.encode('utf-8'))
    return m.hexdigest()


class NameMixin(object):

    def load(self, name):
        return self._load(wrap(name))

    def save(self, name, data):
        return self._save(wrap(name), data)

    def thumbnail(self, name, width, height):
        return self._thumbnail(wrap(name), width, height)

    def has(self, name):
        return self._has(wrap(name))

    def remove(self, name):
        return self._remove(wrap(name))

    def mtime(self, name):
        return self._mtime(wrap(name))

    def cache_timeout(self, name):
        return self._cache_timeout(wrap(name))


class ImfsError(Exception):
    pass


class NotFoundError(ImfsError):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '%s not found' % self.name


class ConnectionError(ImfsError):
    pass


def guarded(f):
    import requests.exceptions
    from functools import wraps

    @wraps(f)
    def g(*args, **kargs):
        try:
            return f(*args, **kargs)
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(str(e))

    return g
