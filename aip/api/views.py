#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from flask import (
    jsonify,
    request,
    render_template,
    current_app,
    g
)
from datetime import datetime
import threading
from functools import wraps
import pickle
import json
from io import BytesIO
from PIL import Image
from base64 import b64encode


def locked(lock=None):
    if lock is None:
        lock = threading.RLock()

    def inner(f):
        @wraps(f)
        def yainner(*args, **kargs):
            with lock:
                return f(*args, **kargs)
        return yainner

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
            r = f(*args, **kargs)
            logging.debug('%s done' % f.__name__)
            return r
        except Exception as e:
            failed(
                f.__name__,
                args=request.args,
                form=request.form,
                json=request.json,
                e=e
            )
            return jsonify(dict(error=dict(message=str(e))))
    return inner


def cast(value):
    if type(value) is bytes:
        return value.decode('utf-8')
    else:
        return value


def tod(o, keys):
    return {k: cast(getattr(o, k)) for k in keys}


def get_slice():
    if request.json and 'begin' in request.json and 'end' in request.json:
        r = slice(request.json['begin'], request.json['end'], 1)
    else:
        r = None
    return r


def _fetch(url):
    return g.http.request('GET', url)


def _fetch_image(url):
    try:
        logging.info('fetch image: %s' % url)
        r = _fetch(url)
        return r.data
    except Exception as e:
        logging.error('fetch image failed: %s' % url)
        logging.exception(e)
        return None


def wrap(entries):
    entries = list(entries)
    if entries:
        for e in entries:
            e.ideal_width = g.column_width
        sm = sorted(entries, key=lambda e: e.score, reverse=True)
        for e in sm[:max(1, int(len(sm) / g.per))]:
            e.ideal_width = g.gutter + 2 * g.column_width
    return entries


def make(app, api, cached, store):
    def get_user_bi_someid():
        if request.json:
            args = request.json
        elif request.form:
            args = request.form
        elif request.args:
            args = request.args
        else:
            args = {}
        if 'user_id' in args:
            user = store.get_user_bi_id(args['user_id'])
        elif 'user_openid' in args:
            user = store.get_user_bi_openid(args['user_openid'])
        else:
            raise Exception('must provider user id or openid')
        return user

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

    @api.route('/entries', methods=['GET'])
    @guarded
    def entries():
        return jsonify(result=[tod(im, ('id',)) for im in store.get_entries_order_bi_ctime(get_slice())])

    @api.route('/page/<int:id>', methods=['GET'])
    @guarded
    def page(id):
        #r = slice(g.per * (2 ** id - 1), g.per * (2 ** (id + 1) - 1), 1)
        r = slice(g.per * id, g.per * (id + 1), 1)
        return jsonify(result=render_template('page.html', entries=wrap(store.get_entries_order_bi_ctime(r))))

    @api.route('/update', defaults={'begin': datetime.today().strftime('%Y%m%d')})
    @api.route('/update/<begin>')
    @guarded
    @locked()
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

    @api.route('/plus', methods=['POST'])
    @guarded
    def plus():
        user = get_user_bi_someid()
        entry = store.get_entry_bi_id(request.json['entry_id'])
        user.plus(entry)
        store.db.session.commit()
        return jsonify(dict(count=entry.plus_count))

    @api.route('/plused/page/<int:id>.html', methods=['GET'])
    @guarded
    def plused_page_html(id):
        user = get_user_bi_someid()
        return jsonify(result=render_template('page.html', entries=wrap(user.plused)))

    @api.route('/plused', methods=['GET'])
    @guarded
    def plused():
        user = get_user_bi_someid()
        return jsonify(result=[tod(e, ('id',)) for e in user.plused])

    @api.route('/minus', methods=['POST'])
    @guarded
    def minus():
        user = get_user_bi_someid()
        entry = store.get_entry_bi_id(request.json['entry_id'])
        user.minus(entry)
        store.db.session.commit()
        return jsonify(dict(count=entry.plus_count))

    @api.route('/sample/<md5>')
    @cached(timeout=24 * 60 * 60)
    def sample(md5):
        md5 = md5.encode('ascii')
        im = store.get_image_bi_md5(md5)
        url = im.sample_url if im.sample_url else im.image_url
        height = im.height
        input_stream = BytesIO(_fetch_image(url))
        im = Image.open(input_stream)
        im.thumbnail((g.sample_width, height), Image.ANTIALIAS)
        output_stream = BytesIO()
        im.save(output_stream, format='JPEG')
        return output_stream.getvalue(), 200, {'Content-Type': 'image/jpeg'}

    @api.route('/proxied_url/<md5>', methods=['GET'])
    @guarded
    @locked()
    def proxied_url(md5):
        md5 = md5.encode('ascii')
        im = store.get_image_bi_md5(md5)
        imgur = store.get_imgur_bi_md5(md5)
        if not imgur:
            fail_count = 0
            while True:
                imgur = make_imgur(im)
                if imgur is not None:
                    break
                if fail_count >= current_app.config['AIP_UPLOAD_IMGUR_RETRY_LIMIT']:
                    break
                logging.info('upload %s to imgur failed, retry' % md5)
                ++fail_count
            if not imgur:
                raise Exception('upload to imgur failed')
            store.db.session.add(imgur)
            store.db.session.commit()
        if 'width' in request.args:
            width = float(request.args['width'])
            height = width * im.height / im.width
            url = best_imgur_link(imgur, width, height)
        else:
            url = imgur.link
        return jsonify(dict(result=url))

    imgur_thumbnails = (
        ('t', 160, 160),
        ('m', 320, 320),
        ('l', 640, 640),
        ('h', 1024, 1024)
    )

    def best_imgur_link(imgur, width, height):
        area = width * height
        ratio = width / height
        for suffix, width, height in imgur_thumbnails:
            if ratio < width / height:
                width = ratio * height
            if area <= current_app.config['AIP_RESOLUTION_LEVEL'] * width * height:
                parts = imgur.link.split('.')
                assert len(parts) > 1
                parts[-2] = parts[-2] + suffix
                return '.'.join(parts)
        return imgur.link

    def make_imgur(im):
        from urllib.request import Request, urlopen
        from urllib.parse import urlencode
        from random import shuffle

        def inner(client_id):
            image_url = im.sample_url if im.sample_url else im.image_url

            def deal(r):
                try:
                    logging.error('make_imgur failed with error code %d and message: %s' % (r['status'], r['data']['error']['message']))
                except:
                    logging.error(r)

                logging.info('download and resize')
                if r['status'] == 400:
                    input_stream = BytesIO(_fetch_image(image_url))
                    im = Image.open(input_stream)
                    limit = current_app.config['AIP_IMGUR_RESIZE_LIMIT']
                    im.thumbnail(
                        (limit, limit),
                        Image.ANTIALIAS
                    )
                    output_stream = BytesIO()
                    im.convert('RGB').save(output_stream, format='JPEG')
                    r = urlopen(Request(
                        'https://api.imgur.com/3/image',
                        headers={'Authorization': 'Client-ID %s' % client_id},
                        data=urlencode({
                            'image': b64encode(output_stream.getvalue()),
                            'type': 'base64'
                        }).encode('ascii')
                    ), timeout=current_app.config['AIP_UPLOAD_IMGUR_TIMEOUT']).read()
                    return json.loads(r.decode('utf-8'))

            try:
                r = urlopen(Request(
                    'https://api.imgur.com/3/image',
                    headers={'Authorization': 'Client-ID %s' % client_id},
                    data=urlencode({
                        'image': image_url,
                        'type': 'URL'
                    }).encode('ascii')
                ), timeout=current_app.config['AIP_UPLOAD_IMGUR_TIMEOUT']).read()
                r = json.loads(r.decode('utf-8'))
                if not r['success']:
                    r = deal(r)
                    if r is None:
                        return None
            except Exception as e:
                logging.error('make_imgur failed')
                logging.exception(e)
                try:
                    r = json.loads(e.read().decode('utf-8'))
                    if not r['success']:
                        r = deal(r)
                        if r is None:
                            return None
                except Exception as e:
                    logging.exception(e)
                    return None

            data = r['data']
            return store.Imgur(
                md5=im.md5,
                id=data['id'].encode('ascii'),
                deletehash=data['deletehash'].encode('ascii'),
                link=data['link']
            )

        client_ids = current_app.config['AIP_IMGUR_CLIENT_IDS'][:]
        shuffle(client_ids)
        for client_id in client_ids:
            logging.info('use client id: %s' % client_id)
            ret = inner(client_id)
            if ret is not None:
                return ret
            logging.info('client id %s failed' % client_id)
        return None

    @api.after_request
    def after_request(response):
        from flask.ext.sqlalchemy import get_debug_queries
        for query in get_debug_queries():
            if query.duration >= current_app.config['DATABASE_QUERY_TIMEOUT']:
                current_app.logger.warning("SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" % (query.statement, query.parameters, query.duration, query.context))
        return response
