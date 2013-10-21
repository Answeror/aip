#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from flask import (
    jsonify,
    request,
    current_app,
    Response,
    g,
    stream_with_context
)
from datetime import datetime, timedelta
import threading
from functools import wraps, partial
from uuid import uuid4
import pickle
from ..async.background import Background
from ..async.subpub import Subpub
import json
import time
from ..layout import render_layout
from fn.iters import chain
from nose.tools import assert_equal


class Log(object):

    @property
    def log(self):
        return logging.getLogger(__name__)

    def info(self, *args, **kargs):
        return self.log.info(*args, **kargs)


log = Log()


def ex():
    return current_app.config['AIP_EXECUTOR']


def fetch_posts(begin, limit, source):
    def gen():
        tags = []
        for _, post in zip(list(range(limit)), source.get_images(tags)):
            if begin is not None and post['ctime'] <= begin:
                break
            yield post
    return list(gen())


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


def logged(f):
    @wraps(f)
    def inner(*args, **kargs):
        try:
            start = time.time()
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
        finally:
            logging.info('%s take %.3fs' % (f.__name__, time.time() - start))
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

    def guarded(f):
        @wraps(f)
        def inner(*args, **kargs):
            try:
                return f(*args, **kargs)
            except Exception as e:
                store.db.session.rollback()

                return jsonify(dict(error=dict(message=str(e))))
        return inner

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

    def format_stream_piece(piece):
        return b'data: ' + piece + b'\n\n'

    def dump_error(message):
        return json.dumps(dict(error=dict(message=message))).encode('utf-8')

    def streamed(f):
        @wraps(f)
        def inner(*args, **kargs):
            def gen():
                try:
                    # to prevent message loss in client EventSouce
                    delay = current_app.config.get('AIP_STREAM_DELAY', 0.01)
                    start = time.time()
                    for piece in f(*args, **kargs):
                        elapsed = float(time.time() - start)
                        if elapsed < delay:
                            time.sleep(delay - elapsed)
                        yield format_stream_piece(piece)
                except Exception as e:
                    yield format_stream_piece(dump_error(str(e)))
            return Response(
                stream_with_context(gen()),
                mimetype='text/event-stream'
            )
        return inner

    def async(rank=0):
        def yainner(f):
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
                ), rank=rank)
                return jsonify(dict(result=dict(id=id)))
            return inner
        return yainner

    def try_get_user_bi_someid():
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
            user = None
        return user

    def get_user_bi_someid():
        user = try_get_user_bi_someid()
        if user is None:
            raise Exception('must provider user id or openid')
        return user

    def arg(key):
        if request.json and key in request.json:
            return request.json[key]
        if request.form and key in request.form:
            return request.form[key]
        if request.args and key in request.args:
            return request.args[key]
        return None

    def require_args(args):
        fields = args

        def gen(f):
            @wraps(f)
            def inner(*args, **kargs):
                for key in fields:
                    value = arg(key)
                    if value is None:
                        return jsonify(dict(error=dict(message='require arg: %s' % key)))
                    kargs[key] = value
                return f(*args, **kargs)
            return inner

        return gen

    def optional_args(args):
        fields = args

        def gen(f):
            @wraps(f)
            def inner(*args, **kargs):
                for field in fields:
                    try:
                        key, kind = field
                    except:
                        key, kind = field, str
                    value = arg(key)
                    if value is not None:
                        kargs[key] = kind(value)
                return f(*args, **kargs)
            return inner

        return gen

    def _set_last_update_time(value):
        store.set_meta('last_update_time', pickle.dumps(value))

    def _update_images(begin=None, limit=65536):
        start = time.time()
        sources = [make(dict) for make in g.sources]

        from concurrent.futures import ThreadPoolExecutor as Ex
        with Ex(len(sources)) as ex:
            posts = list(chain.from_iterable(
                ex.map(partial(fetch_posts, begin, limit), sources)
            ))

        log.info('fetch posts done, %d fetched, take %.4fs' % (len(posts), time.time() - start))
        with store.autodag() as dag:
            store.Post.puts(dag=dag, posts=posts)

    @api.route('/add_user', methods=['POST'])
    @guarded
    @logged
    def add_user():
        store.add_user(
            openid=request.json['openid'],
            name=request.json['name'],
            email=request.json['email']
        )
        store.db.session.commit()
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
        return jsonify(result=[tod(im, ('id', 'md5')) for im in store.get_entries_order_bi_ctime(get_slice())])

    def authed():
        return try_get_user_bi_someid() is not None


    def page_ext(id):
        #r = slice(g.per * (2 ** id - 1), g.per * (2 ** (id + 1) - 1), 1)
        r = slice(g.per * id, g.per * (id + 1), 1)

        if request.args and 'tags' in request.args:
            tags = request.args['tags'].split(';')
            logging.debug('query tags: {}'.format(tags))
            tags = [store.Tag.escape_name(tag) for tag in tags if tag]
        else:
            tags = []

        return store.Entry.get_bi_tags_order_bi_ctime(
            tags=tags,
            r=r,
            safe=not authed()
        )

    @api.route('/page/<int:id>', methods=['GET'])
    @guarded
    @logged
    def page(id):
        return jsonify(result=render_layout('page.html', entries=page_ext(id)))

    @api.route('/stream/page/<int:id>', methods=['GET'])
    @logged
    @streamed
    def stream_page(id):
        yield dump_result(render_layout('page.html', entries=page_ext(id)))

    @api.route('/update', defaults={'begin': (datetime.utcnow() - timedelta(days=1)).strftime('%Y%m%d%H%M%S')})
    @api.route('/update/<begin>')
    @guarded
    @logged
    def update(begin):
        now = datetime.utcnow()
        begin = datetime.strptime(begin, '%Y%m%d%H%M%S')
        _update_images(begin)
        _set_last_update_time(now)
        store.db.session.commit()
        return jsonify(dict())

    @api.route('/update/past/<int:seconds>')
    @guarded
    @logged
    def update_past(seconds):
        now = datetime.utcnow()
        _update_images(now - timedelta(seconds=seconds))
        _set_last_update_time(now)
        store.db.session.commit()
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

    @guarded
    @logged
    @require_args(['user_id', 'entry_id'])
    def plus(user_id, entry_id):
        store.plus(user_id, entry_id)
        store.db.session.commit()
        return jsonify(dict(count=store.plus_count(entry_id)))

    @api.route('/plus', methods=['POST'])
    @guarded
    @logged
    def sync_plus():
        return plus()

    @api.route('/async/<sid>/plus', methods=['POST'])
    @guarded
    @logged
    @async(rank=app.config['AIP_RANK_PLUS'])
    def async_plus(sid):
        return plus()

    def dump_result(*args, **kargs):
        if args:
            assert_equal(len(args), 1)
            arg = args[0]
        else:
            arg = kargs
        return json.dumps(dict(result=arg)).encode('utf-8')

    @api.route('/stream/plus', methods=['GET'])
    @logged
    @streamed
    @require_args(['user_id', 'entry_id'])
    def stream_plus(user_id, entry_id):
        store.plus(user_id, entry_id)
        store.db.session.commit()
        yield dump_result(count=store.plus_count(entry_id))

    @api.route('/stream/minus', methods=['GET'])
    @logged
    @streamed
    @require_args(['user_id', 'entry_id'])
    def stream_minus(user_id, entry_id):
        store.minus(user_id, entry_id)
        store.db.session.commit()
        yield dump_result(count=store.plus_count(entry_id))

    @api.route('/plused/page/<int:id>.html', methods=['GET'])
    @guarded
    @logged
    def plused_page_html(id):
        user = get_user_bi_someid()
        r = slice(g.per * id, g.per * (id + 1), 1)
        return jsonify(result=render_layout('page.html', entries=wrap(user.get_plused(r))))

    @api.route('/stream/plused/page/html/<int:id>', methods=['GET'])
    @logged
    @streamed
    def stream_plused_page_html(id):
        user = get_user_bi_someid()
        r = slice(g.per * id, g.per * (id + 1), 1)
        yield dump_result(render_layout('page.html', entries=wrap(user.get_plused(r))))

    @api.route('/plused', methods=['GET'])
    @guarded
    @logged
    def plused():
        user = get_user_bi_someid()
        return jsonify(result=[dict(id=p.entry.id, ctime=p.ctime) for p in user.plused])

    @guarded
    @logged
    @require_args(['user_id', 'entry_id'])
    def minus(user_id, entry_id):
        store.minus(user_id, entry_id)
        store.db.session.commit()
        return jsonify(dict(count=store.plus_count(entry_id)))

    @api.route('/minus', methods=['POST'])
    @guarded
    @logged
    def sync_minus():
        return minus()

    @api.route('/async/<sid>/minus', methods=['POST'])
    @guarded
    @logged
    @async(rank=app.config['AIP_RANK_MINUS'])
    def async_minus(sid):
        return minus()

    def imgur_url(md5, width=None, resolution=None):
        from .. import proxy
        return proxy.imgur_url(store, md5, width=width, resolution=resolution)

    def imgur_url_gen(md5, width=None, resolution=None):
        from .. import proxy
        yield from proxy.imgur_url_gen(store, md5, width=width, resolution=resolution)

    def immio_url(md5):
        from .. import proxy
        return proxy.immio_url(store, md5)

    @guarded
    @logged
    def proxied_url(md5):
        for make in (imgur_url, ):
            logging.info('use %s' % make.__name__)
            try:
                uri = make(md5)
                logging.info('get %s' % uri)
                return jsonify(dict(result=uri))
            except Exception as e:
                logging.exception(e)
        raise Exception('all gallery failed')

    @api.route('/proxied_url/<md5>', methods=['GET'])
    @guarded
    @logged
    def sync_proxied_url(md5):
        return proxied_url(md5)

    @api.route('/async/<sid>/proxied_url/<md5>', methods=['GET'])
    @guarded
    @logged
    @async()
    def async_proxied_url(sid, md5):
        return proxied_url(md5)

    @api.route('/stream/proxied_url/<md5>', methods=['GET'])
    @logged
    @streamed
    @optional_args([('width', float), ('resolution', float)])
    def stream_proxied_url(md5, width=None, resolution=None):
        for make in (imgur_url_gen, ):
            logging.info('use %s' % make.__name__)
            try:
                for uri in make(md5=md5, width=width, resolution=resolution):
                    logging.info('get %s' % uri)
                    yield dump_result(uri)
            except Exception as e:
                logging.exception(e)
        raise Exception('all gallery failed')

    @api.after_request
    def after_request(response):
        from flask.ext.sqlalchemy import get_debug_queries
        for query in get_debug_queries():
            if query.duration >= current_app.config['DATABASE_QUERY_TIMEOUT']:
                current_app.logger.warning("SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" % (query.statement, query.parameters, query.duration, query.context))
        return response
