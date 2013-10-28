import hashlib
from time import time
from functools import wraps
from .log import Log


log = Log(__name__)


def md5(data):
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


def timed(f):
    @wraps(f)
    def inner(*args, **kargs):
        try:
            start = time()
            return f(*args, **kargs)
        finally:
            log.info('%s take %.4f', f.__name__, float(time() - start))
    return inner
