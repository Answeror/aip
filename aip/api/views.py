#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import inspect
from flask import (
    jsonify,
    request,
    g
)
from datetime import datetime
import threading
from functools import wraps
import pickle
from .. import store


lock = threading.RLock()


def locked(f):
    @wraps(f)
    def inner(*args, **kargs):
        with lock:
            return f(*args, **kargs)
    return inner


def failed(name, args=None, form=None, json=None, e=None):
    lines = ['{} failed'.format(name)]
    if args:
        lines.append('args: {}'.format(args))
    if form:
        lines.append('form: {}'.format(form))
    if json:
        lines.append('json: {}'.format(json))
    logging.error('\n'.join(lines))
    if e:
        logging.exception(e)


def guarded(f):
    @wraps(f)
    def inner(*args, **kargs):
        try:
            return f(*args, **kargs)
        except Exception as e:
            failed(
                f.__name__,
                args=response.args,
                form=response.form,
                json=response.json
            )
            return jsonify(dict(error=dict(message=str(e))))
    return inner


def _tod(entry):
    return {'id': entry.id.decode('ascii')}


def _set_last_update_time(value):
    store.set_meta('last_update_time', pickle.dumps(value))
    store.db.session.commit()


def _update_images(begin=None, limit=65536):
    for make in g.sources:
        source = make(store.Post)
        tags = []
        for i, im in zip(list(range(limit)), source.get_images(tags)):
            if begin is not None and im.ctime <= begin:
                break
            store.put_image(im)
        store.db.session.commit()


def make(app, api):

    @api.route('/add_user', methods=['POST'])
    @guarded
    def add_user():
        store.add_user(store.User(
            openid=request.json['openid'],
            name=request.json['name'],
            email=request.json['email']
        ))
        return jsonify(dict())

    @api.route('/user_count')
    @guarded
    def user_count():
        return jsonify(dict(result=store.user_count()))

    @api.route('/image_count')
    @guarded
    def image_count():
        return jsonify(dict(result=store.image_count()))

    @api.route('/unique_image_count')
    @guarded
    def unique_image_count():
        return jsonify(dict(result=store.unique_image_count()))

    @api.route('/entry_count')
    @guarded
    def entry_count():
        return jsonify(dict(result=store.entry_count()))

    @api.route('/entries')
    @guarded
    def entries():
        return jsonify(result=[_tod(im) for im in store.get_entries_order_bi_ctime()])

    @api.route('/update', defaults={'begin': datetime.today().strftime('%Y%m%d')})
    @api.route('/update/<begin>')
    @guarded
    @locked
    def update(begin=None):
        from datetime import datetime
        begin = datetime.strptime(begin, '%Y%m%d')
        _set_last_update_time(datetime.now())
        _update_images(begin)
        return jsonify(dict())

    @api.route('/last_update_time')
    @guarded
    def last_update_time():
        value = store.get_meta('last_update_time')
        value = '' if value is None else pickle.loads(value).strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(dict(result=value))

    @api.route('/clear')
    @guarded
    def clear():
        store.clear()
        return jsonify(dict())
