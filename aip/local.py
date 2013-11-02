from werkzeug.local import LocalProxy
from flask import (
    current_app,
    session,
    request,
    g,
)
import json
import threading


def get_user_bi_someid():
    if 'openid' in session:
        user = core.user_bi_openid(session['openid'])
    else:
        if current_app.config.get('AIP_DEBUG', False):
            user = core.user_bi_id(1)
    return user


def authed():
    try:
        return get_current_user() is not None
    except:
        return False


def get_core():
    core = getattr(g, '_core', None)
    if core is None:
        core = g._core = current_app._core
    return core


core = LocalProxy(get_core)


def get_current_user():
    if not hasattr(g, '_current_user'):
        g._current_user = get_user_bi_someid()
    return g._current_user


current_user = LocalProxy(get_current_user)


def get_request_kargs():
    d = getattr(g, '_request_kargs', None)
    if d is None:
        d = {}
        if request.method == 'GET':
            d.update(request.args)
        else:
            d.update(json.loads(request.data.decode('utf-8')))
        g._request_kargs = d
    return d


request_kargs = LocalProxy(get_request_kargs)

thread_slave_lock = threading.RLock()


def get_thread_slave():
    s = getattr(g, '_thread_slave', None)
    if s is None:
        with thread_slave_lock:
            if not hasattr(current_app, '_thread_slave'):
                current_app._thread_slave = make_thread_slave(
                    current_app.config['AIP_THREAD_SLAVE_COUNT']
                )
        s = g._thread_slave = current_app._thread_slave
    return s


thread_slave = LocalProxy(get_thread_slave)


def make_thread_slave(slave_count):
    from concurrent.futures import ThreadPoolExecutor as Ex
    ex = Ex(slave_count)

    def cleanup():
        ex.shutdown()

    import atexit
    atexit.register(cleanup)

    return ex


def since_last_update():
    import pickle
    from datetime import datetime
    t = g.last_update_time
    t = datetime(year=1970, month=1, day=1) if t is None else pickle.loads(t)
    return t
