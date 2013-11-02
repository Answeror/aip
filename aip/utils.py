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
    return _timed(f, 'info')


def profed(f):
    from .log import Tee
    from flask import current_app
    import os
    from profilehooks import profile
    from contextlib import closing

    @wraps(f)
    def g(*args, **kargs):
        with closing(Tee(
            os.path.join(current_app.config['AIP_TEMP_PATH'], 'prof'),
            'a'
        )):
            return profile(immediate=True)(f)(*args, **kargs)
    return g


def debug_timed(f):
    return _timed(profed(f), 'debug')


def _timed(f, level):
    @wraps(f)
    def g(*args, **kargs):
        try:
            start = time()
            return f(*args, **kargs)
        finally:
            getattr(log, level)('{} take {}', f.__name__, time() - start)
    return g


def thumbmd5(md5, width):
    return calcmd5(('%s.%d' % (md5, width)).encode('ascii'))


def require(fields):
    from .local import request_kargs
    from flask import jsonify

    def gen(f):
        @wraps(f)
        def g(*args, **kargs):
            for key in fields:
                value = request_kargs.get(key)
                if value is None:
                    return jsonify({
                        'error': {
                            'message': 'require arg: %s' % key
                        }
                    })
                kargs[key] = value
            return f(*args, **kargs)
        return g

    return gen


def init_session_retry(session, max_retries):
    from requests.adapters import HTTPAdapter
    from nose.tools import assert_greater_equal
    assert_greater_equal(max_retries, 0)
    session.mount('http://', HTTPAdapter(max_retries=max_retries))
    session.mount('https://', HTTPAdapter(max_retries=max_retries))
