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


def _failed(args=None, form=None, e=None):
    lines = ['{} failed'.format(inspect.stack()[1][3])]
    if args:
        lines.append('args: {}'.format(args))
    if form:
        lines.append('form: {}'.format(form))
    logging.error('\n'.join(lines))
    if e:
        logging.exception(e)


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
    def add_user():
        try:
            store.add_user(store.User(
                openid=request.form['openid'],
                name=request.form['name'],
                email=request.form['email']
            ))
            return jsonify(dict(result=True))
        except Exception as e:
            _failed(e=e, form=request.form)
            return jsonify(dict(result=False))

    @api.route('/user_count')
    def user_count():
        try:
            return jsonify(dict(result=store.user_count()))
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(error=dict(message=str(e))))

    @api.route('/image_count')
    def image_count():
        try:
            return jsonify(dict(result=store.image_count()))
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(error=dict(message=str(e))))

    @api.route('/unique_image_count')
    def unique_image_count():
        try:
            return jsonify(dict(result=store.unique_image_count()))
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(error=dict(message=str(e))))

    @api.route('/entry_count')
    def entry_count():
        try:
            return jsonify(dict(result=store.entry_count()))
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(error=dict(message=str(e))))

    @api.route('/entries')
    def entries():
        try:
            return jsonify(result=[
                _tod(im) for im in store.get_entries_order_bi_ctime()
            ])
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(error=dict(message=str(e))))

    @api.route('/update', defaults={'begin': datetime.today().strftime('%Y%m%d')})
    @api.route('/update/<begin>')
    @locked
    def update(begin=None):
        try:
            from datetime import datetime
            begin = datetime.strptime(begin, '%Y%m%d')
            _set_last_update_time(datetime.now())
            _update_images(begin)
            return jsonify(dict(result=True))
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(result=False))

    @api.route('/last_update_time')
    def last_update_time():
        try:
            value = store.get_meta('last_update_time')
            value = '' if value is None else pickle.loads(value).strftime('%Y-%m-%d %H:%M:%S')
            return jsonify(dict(result=value))
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(error=dict(message=str(e))))

    @api.route('/clear')
    def clear():
        try:
            store.clear()
            return jsonify(dict(result=True))
        except Exception as e:
            _failed(e=e)
            return jsonify(dict(result=False))
