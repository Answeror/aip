import hashlib
from time import time
from functools import wraps
from .log import Log


log = Log(__name__)


def md5(data):
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


calcmd5 = md5


def timed(f):
    @wraps(f)
    def inner(*args, **kargs):
        try:
            start = time()
            return f(*args, **kargs)
        finally:
            log.info('{} take {}', f.__name__, time() - start)
    return inner


def thumbmd5(md5, width):
    return calcmd5(('%s.%d' % (md5, width)).encode('ascii'))
