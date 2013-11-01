from werkzeug.local import LocalProxy
from flask import (
    current_app,
    request,
    session,
    g,
)


def get_user_bi_someid():
    args = {}
    if request.form:
        args.update(request.form)
    if request.json:
        args.update(request.json)
    if request.args:
        args.update(request.args)
    args.update(session)

    if 'user_id' in args:
        user = core.user_bi_id(args['user_id'])
    elif 'user_openid' in args:
        user = core.user_bi_openid(args['user_openid'])
    else:
        user = None
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
