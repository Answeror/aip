#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from flask import (
    jsonify,
    request,
    render_template,
    current_app,
    Response,
    g
)
from datetime import datetime
import threading
from functools import wraps
from uuid import uuid4
import pickle
from ..imgur import Imgur
from ..bed.immio import Immio
from ..async.background import Background
from ..async.subpub import Subpub
import json


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
            return f(*args, **kargs)
        except Exception as e:
            return jsonify(dict(error=dict(message=str(e))))
    return inner


def logged(f):
    @wraps(f)
    def inner(*args, **kargs):
        try:
            logging.info('%s start' % f.__name__)
            r = f(*args, **kargs)
            logging.info('%s done' % f.__name__)
            return r
        except Exception as e:
            failed(
                f.__name__,
                args=request.args,
                form=request.form,
                json=request.json,
                e=e
            )
            raise
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


def wrap(entries):
    return entries


def make(app, api, cached, store):
    api.b = Background(slave_count=app.config.get('AIP_SLAVE_COUNT', 1))
    api.b.start()
    api.sp = Subpub()

    def event_stream(sid):
        hello_count = 0
        again = True
        timeout = 1
        while again:
            try:
                key, value = api.sp.pop(sid, timeout=timeout)
                timeout = app.config['AIP_STREAM_EVENT_TIMEOUT']
                logging.info('stream(%s) event: %s' % (sid, key))
                if key == 'reply':
                    hello_count = 0
                else:
                    yield b'data: ' + value + b'\n\n'
            except Exception as e:
                if str(e) == 'timeout':
                    logging.info('stream event timeout: %s' % sid)
                    if hello_count >= app.config['AIP_STREAM_HELLO_LIMIT']:
                        logging.info('close stream %s' % sid)
                        api.sp.kill(sid)
                        again = False
                    else:
                        hello(sid)
                        hello_count += 1
                else:
                    logging.error('event stream failed')
                    logging.exception(e)
                    api.sp.kill(sid)
                    again = False
                    raise

    def hello(sid):
        data = json.dumps(dict(
            key='hello',
            value=sid
        )).encode('utf-8')
        api.sp.push(sid, ('hello', data))

    @api.route('/async/reply/<sid>', methods=['POST'])
    def reply(sid):
        api.sp.push(sid, ('reply', None))
        return jsonify(dict())

    @api.route('/async/stream/<sid>')
    @logged
    def stream(sid):
        logging.info('stream: %s' % sid)
        return Response(event_stream(sid), mimetype='text/event-stream')

    def async(f):
        @wraps(f)
        def inner(*args, **kargs):
            # save request data
            request_kargs = {}
            for key in (
                'path',
                'base_url',
                'query_string',
                'method',
                'data',
            ):
                request_kargs[key] = getattr(request, key)
            request_kargs['query_string'] = request.args if request.args else {}
            request_kargs['headers'] = request.headers.items()
            request_kargs['content_type'] = request.headers['Content-Type']

            def g():
                # restore request data
                with app.test_request_context(**request_kargs):
                    return f(*args, **kargs)

            if args:
                sid = args[0]
            else:
                sid = kargs['sid']
            id = str(uuid4())
            api.b.function(g, lambda a: api.sp.push(
                sid, (
                    'result',
                    json.dumps(dict(
                        key='result',
                        value=dict(
                            id=id,
                            result=json.loads(a.data.decode('utf-8'))
                        )
                    )).encode('utf-8')
                )
            ))
            return jsonify(dict(result=dict(id=id)))
        return inner

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
            source = make(store.Post.from_tag_names)
            tags = []
            for i, im in zip(list(range(limit)), source.get_images(tags)):
                if begin is not None and im.ctime <= begin:
                    break
                store.put_image(im)
            store.db.session.commit()

    @api.route('/add_user', methods=['POST'])
    @guarded
    @logged
    def add_user():
        store.add_user(store.User(
            openid=request.json['openid'],
            name=request.json['name'],
            email=request.json['email']
        ))
        return jsonify(dict())

    @api.route('/user_count')
    @guarded
    @logged
    def user_count():
        return jsonify(dict(result=store.user_count()))

    @api.route('/image_count')
    @guarded
    @logged
    def image_count():
        return jsonify(dict(result=store.image_count()))

    @api.route('/unique_image_count')
    @guarded
    @logged
    def unique_image_count():
        return jsonify(dict(result=store.unique_image_count()))

    @api.route('/entry_count')
    @guarded
    @logged
    def entry_count():
        return jsonify(dict(result=store.entry_count()))

    @api.route('/entries', methods=['GET'])
    @guarded
    @logged
    def entries():
        return jsonify(result=[tod(im, ('id',)) for im in store.get_entries_order_bi_ctime(get_slice())])

    @api.route('/page/<int:id>', methods=['GET'])
    @guarded
    @logged
    def page(id):
        #r = slice(g.per * (2 ** id - 1), g.per * (2 ** (id + 1) - 1), 1)
        r = slice(g.per * id, g.per * (id + 1), 1)
        logging.debug('request args {}'.format(request.args))
        if request.args and 'tags' in request.args:
            tags = request.args['tags'].split(';')
            es = store.Entry.get_bi_tags_order_bi_ctime(tags=tags, r=r)
        else:
            es = wrap(store.get_entries_order_bi_ctime(r))
        return jsonify(result=render_template('page.html', entries=es))

    @api.route('/update', defaults={'begin': datetime.today().strftime('%Y%m%d')})
    @api.route('/update/<begin>')
    @guarded
    @logged
    @locked()
    def update(begin=None):
        from datetime import datetime
        begin = datetime.strptime(begin, '%Y%m%d')
        _set_last_update_time(datetime.now())
        _update_images(begin)
        return jsonify(dict())

    @api.route('/last_update_time')
    @guarded
    @logged
    def last_update_time():
        value = store.get_meta('last_update_time')
        value = '' if value is None else pickle.loads(value).strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(dict(result=value))

    @api.route('/clear')
    @guarded
    @logged
    def clear():
        store.clear()
        return jsonify(dict())

    def plus():
        try:
            user = get_user_bi_someid()
            entry = store.get_entry_bi_id(request.json['entry_id'])
            user.plus(entry)
            return jsonify(dict(count=entry.plus_count))
        except:
            store.db.session.rollback()
            raise

    @api.route('/plus', methods=['POST'])
    @guarded
    @logged
    def sync_plus():
        return plus()

    @api.route('/async/<sid>/plus', methods=['POST'])
    @guarded
    @logged
    @async
    def async_plus(sid):
        return plus()

    @api.route('/plused/page/<int:id>.html', methods=['GET'])
    @guarded
    @logged
    def plused_page_html(id):
        user = get_user_bi_someid()
        return jsonify(result=render_template('page.html', entries=wrap(user.plused_entries)))

    @api.route('/plused', methods=['GET'])
    @guarded
    @logged
    def plused():
        user = get_user_bi_someid()
        return jsonify(result=[tod(e, ('id',)) for e in user.plused])

    def minus():
        try:
            user = get_user_bi_someid()
            entry = store.get_entry_bi_id(request.json['entry_id'])
            user.minus(entry)
            return jsonify(dict(count=entry.plus_count))
        except:
            store.db.session.rollback()
            raise

    @api.route('/minus', methods=['POST'])
    @guarded
    @logged
    def sync_minus():
        return minus()

    @api.route('/async/<sid>/minus', methods=['POST'])
    @guarded
    @logged
    @async
    def async_minus(sid):
        return minus()

    def imgur_url(md5):
        im = store.get_image_bi_md5(md5)
        imgur_image = store.get_imgur_bi_md5(md5)
        limit = current_app.config['AIP_IMGUR_RESIZE_LIMIT']
        imgur = Imgur(
            client_ids=current_app.config['AIP_IMGUR_CLIENT_IDS'],
            resolution_level=current_app.config['AIP_RESOLUTION_LEVEL'],
            max_size=(limit, limit),
            timeout=current_app.config['AIP_UPLOAD_IMGUR_TIMEOUT'],
            album_deletehash=current_app.config['AIP_IMGUR_ALBUM_DELETEHASH'],
            http=g.http
        )
        if not imgur_image:
            fail_count = 0
            while True:
                imgur_image = imgur.upload(im)
                if imgur_image is not None:
                    imgur_image = store.Imgur(
                        id=imgur_image.id,
                        md5=imgur_image.md5,
                        link=imgur_image.link,
                        deletehash=imgur_image.deletehash
                    )
                    break
                if fail_count >= current_app.config['AIP_UPLOAD_IMGUR_RETRY_LIMIT']:
                    break
                logging.info('upload %s to imgur failed, retry' % md5)
                ++fail_count
            if not imgur_image:
                raise Exception('upload to imgur failed')
            store.db.session.add(imgur_image)
            store.db.session.commit()
        if 'width' in request.args:
            width = float(request.args['width'])
            height = width * im.height / im.width
            url = imgur.best_link(imgur_image, width, height)
        else:
            url = imgur_image.link
        return url

    def immio_url(md5):
        im = store.get_image_bi_md5(md5)
        immio_image = store.get_immio_bi_md5(md5)
        immio = Immio(
            max_size=current_app.config['AIP_IMMIO_RESIZE_MAX_SIZE'],
            timeout=current_app.config['AIP_UPLOAD_IMMIO_TIMEOUT'],
            http=g.http
        )
        if immio_image:
            logging.info('hit %s' % md5)
        else:
            immio_image = immio.upload(im)
            if immio_image is not None:
                immio_image = store.Immio(
                    uid=immio_image.uid,
                    md5=immio_image.md5,
                    uri=immio_image.uri,
                    width=immio_image.width,
                    height=immio_image.height
                )
            if not immio_image:
                raise Exception('upload to immio failed')
            immio_image = store.db.session.merge(immio_image)
            store.db.session.add(immio_image)
            store.db.session.commit()
        return immio_image.uri

    @locked()
    def proxied_url(md5):
        for make in (immio_url, imgur_url):
            logging.info('use %s' % make.__name__)
            try:
                uri = make(md5)
                logging.info('get %s' % uri)
                return jsonify(dict(result=uri))
            except Exception as e:
                logging.error(e)
        return jsonify(dict(error=dict(message='all gallery failed')))

    @api.route('/proxied_url/<md5>', methods=['GET'])
    @guarded
    @logged
    def sync_proxied_url(md5):
        return proxied_url(md5)

    @api.route('/async/<sid>/proxied_url/<md5>', methods=['GET'])
    @guarded
    @logged
    @async
    def async_proxied_url(sid, md5):
        return proxied_url(md5)

    @api.after_request
    def after_request(response):
        from flask.ext.sqlalchemy import get_debug_queries
        for query in get_debug_queries():
            if query.duration >= current_app.config['DATABASE_QUERY_TIMEOUT']:
                current_app.logger.warning("SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" % (query.statement, query.parameters, query.duration, query.context))
        return response
