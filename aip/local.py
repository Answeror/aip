from werkzeug.local import LocalProxy
from flask import (
    current_app,
    session,
    request,
    g,
)


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
        for name in ('form', 'json', 'args'):
            if getattr(request, name):
                d.update(getattr(request, name))
        g._request_kargs = d
    return d


request_kargs = LocalProxy(get_request_kargs)
