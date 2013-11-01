#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import re
from flask import (
    jsonify,
    g,
    session,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    render_template,
    abort,
    Response,
)
from operator import attrgetter as attr
from collections import namedtuple
from urllib.parse import urlparse, urlunparse
from .layout import render_layout
from functools import wraps
from .log import Log
from time import time
from .utils import md5 as calcmd5
from . import img
from datetime import datetime, timedelta
from . import work
import scss
from collections import OrderedDict
from . import tasks
from .utils import timed
from nose.tools import assert_in, assert_is
import json


Post = namedtuple('Post', (
    'url',
    'preview_url',
    'preview_width',
    'preview_height',
    'md5'
))


log = Log(__name__)


def _scale(entries):
    images = [e.best_post for e in entries]
    posts = []
    if images:
        for im in images:
            im.scale = g.column_width
        sm = sorted(images, key=attr('score'), reverse=True)
        for im in sm[:max(1, int(len(sm) / current_app.config['AIP_PER']))]:
            im.scale = g.gutter + 2 * g.column_width
        for im in images:
            preview_height = int(im.scale * im.height / im.width)
            preview_width = int(im.scale)
            posts.append(Post(
                url=im.post_url,
                preview_url=im.preview_url,
                preview_height=preview_height,
                preview_width=preview_width,
                md5=im.md5
            ))
    return posts


def _ensure_exists(path):
    assert os.path.exists(path), 'file not exist: %s' % path


def prop(f):
    setattr(g.__class__, f.__name__, property(f))


@prop
def http(self):
    if not hasattr(g, '_http'):
        import urllib3
        g._http = urllib3.PoolManager()
    return g._http


@prop
def url_for_page():
    def inner(page):
        args = request.view_args.copy()
        args['page'] = page
        return url_for(request.endpoint, **args)
    return inner


@prop
def sources(self):
    if not hasattr(g, '_sources'):
        g._sources = []
        import pkgutil
        import importlib
        from inspect import isabstract
        from . import sources
        sources_folder = os.path.dirname(sources.__file__)
        for _, name, _ in list(pkgutil.iter_modules([sources_folder])):
            module = importlib.import_module('.sources.' + name, 'aip')
            if hasattr(module, 'Source'):
                source = getattr(module, 'Source')
                if not isabstract(source):
                    g._sources.append(source)
    return g._sources


@prop
def sample_width(self):
    return current_app.config['AIP_SAMPLE_WIDTH']


@prop
def column_width(self):
    return current_app.config['AIP_COLUMN_WIDTH']


@prop
def gutter(self):
    return current_app.config['AIP_GUTTER']


@prop
def per(self):
    return current_app.config['AIP_PER']


def _fetch(url):
    return g.http.request('GET', url)


def timestamp(endpoint):
    d = current_app.config.get('AIP_TIMESTAMP', {})
    return d.get(endpoint, None)


def set_timestamp(endpoint, value):
    d = current_app.config.get('AIP_TIMESTAMP', {})
    d[endpoint] = value
    current_app.config['AIP_TIMESTAMP'] = d


def timestamped(endpoint):
    def gen(f):
        @wraps(f)
        def inner(*args, **kargs):
            r = f(*args, **kargs)
            if hasattr(r, 'content_md5') and r.content_md5:
                set_timestamp(endpoint, r.content_md5)
            return r
        return inner
    return gen


def has_timestamp():
    return current_app.config['AIP_TIMESTAMP_FIELD'] in request.args


def dated_url_for(endpoint, **values):
    if timestamp(endpoint) is not None:
        values[current_app.config['AIP_TIMESTAMP_FIELD']] = timestamp(endpoint)
    return url_for(endpoint, **values)


def make(app, oid, cached, store):

    from .momentjs import momentjs
    app.jinja_env.globals['momentjs'] = momentjs

    core = app.core

    @app.context_processor
    def override_url_for():
        return dict(url_for=dated_url_for)

    @prop
    def last_update_time(self):
        return store.get_meta('last_update_time')

    @app.before_request
    def lookup_current_user():
        g.user = None
        if 'openid' in session:
            g.user = store.get_user_bi_openid(session['openid'])
        elif 'id' in session:
            g.user = store.get_user_bi_id(session['id'])
        #else:
            #g.user = store.get_user_bi_id(1)

    @app.route('/login', methods=['GET', 'POST'])
    @oid.loginhandler
    def login():
        if g.user is not None:
            return redirect(oid.get_next_url())
        return try_login()

    @oid.after_login
    def create_or_login(resp):
        if g.user is not None:
            flash('Successfully signed in')
            return redirect(oid.get_next_url())

        if 'openid' in session:
            log.info('openid %s already in session' % session['openid'])
            if store.Openid.exists(resp.identity_url):
                log.info(
                    'group openid %s with %s',
                    resp.identity_url,
                    session['openid']
                )
                store.User.group_openid(resp.identity_url, session['openid'])
                return redirect(url_for('.posts'))

        session['openid'] = resp.identity_url
        return redirect(url_for(
            '.create_profile',
            next=oid.get_next_url(),
            name=resp.fullname or resp.nickname,
            email=resp.email
        ))

    def replace_base_url(uri):
        p = list(urlparse(uri))
        p[0] = app.config.get('AIP_SCHEME', p[0])
        p[1] = app.config.get('AIP_NETLOC', p[1])
        return urlunparse(p)

    def try_login():
        request.base_url = replace_base_url(request.base_url)
        request.host_url = replace_base_url(request.host_url)
        openid = 'https://www.google.com/accounts/o8/id'
        return oid.try_login(
            openid,
            ask_for=['email', 'fullname', 'nickname']
        )

    @app.route('/create_profile', methods=['GET', 'POST'])
    def create_profile():
        if g.user is not None or 'openid' not in session:
            return redirect(url_for('.posts'))
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            if not name:
                flash('Error: you have to provide a name')
            elif '@' not in email:
                flash('Error: you have to enter a valid email address')
            else:
                user = store.User.get_bi_email(email)
                if user:
                    return try_login()
                else:
                    flash('Profile successfully created')
                    user = store.add_user(
                        name=name,
                        email=email,
                        openid=session['openid']
                    )
                    store.db.session.commit()
                    return redirect(oid.get_next_url())
        return render_layout(
            'create_profile.html',
            next_url=oid.get_next_url()
        )

    @app.route('/logout')
    def logout():
        session.pop('openid', None)
        flash('You were signed out')
        return redirect(oid.get_next_url())

    @app.route('/')
    def posts():
        tags = request.args.get('q', '')
        return render_layout('index.html', tags=tags)

    @app.route('/plused')
    def plused():
        return render_layout('plused.html')

    def scss_sources(root):
        sources = []
        for filename in os.listdir(root):
            if re.match(r'aip-\w+\.scss', filename):
                with open(os.path.join(root, filename), 'rb') as f:
                    content = f.read().decode('utf-8')
                sources.append((filename, content))
        return sources

    def expired_request(mtime):
        try:
            return (
                'if-modified-since' not in request.headers or
                datetime.strptime(
                    request.headers['if-modified-since'],
                    '%a, %d %b %Y %H:%M:%S GMT'
                ) + timedelta(seconds=1) < mtime
            )
        except ValueError:
            log.info(
                'wrong if-modified-since format: %s',
                request.headers['if-modified-since']
            )
            return True

    @app.route('/style.css')
    @timestamped('.style')
    def style():
        root = os.path.join(app.static_folder, 'scss')
        sources = scss_sources(root)

        def gen():
            for filename, _ in sources:
                yield datetime.fromtimestamp(os.path.getmtime(os.path.join(
                    root,
                    filename
                )))
        mtime = max(gen())

        if has_timestamp() and not expired_request(mtime):
            return Response(status=304)

        c = scss.Scss(
            scss_vars={},
            scss_opts={
                'compress': True,
                'debug_info': True,
                'load_paths': [root]
            }
        )
        c._scss_files = OrderedDict(sources)
        content = c.compile()
        resp = Response(
            content,
            mimetype='text/css',
        )
        resp.content_md5 = calcmd5(content.encode('utf-8'))
        resp.last_modified = mtime

        if has_timestamp():
            if cache_timeout() is not None:
                resp.cache_control.max_age = cache_timeout()
                resp.expires = int(time() + cache_timeout())

        return resp

    @app.route('/js')
    @timestamped('.js')
    def js():
        names = [
            'head.js',
            'ut.js',
            'notice.js',
            'redo.js',
            'stream.js',
            'super_resolution.js',
            'load_image.js',
            'plus.js',
            'detail.js',
            'tag.js',
            'thumbnail.js',
            'fade.js',
            'base.js',
        ]

        def gen():
            for name in names:
                yield datetime.fromtimestamp(os.path.getmtime(os.path.join(
                    current_app.root_path,
                    current_app.template_folder,
                    name
                )))
        mtime = max(gen())

        if has_timestamp() and not expired_request(mtime):
            return Response(status=304)

        content = '\n'.join(render_template(name) for name in names)
        resp = Response(
            content,
            mimetype='text/javascript',
        )
        resp.content_md5 = calcmd5(content.encode('utf-8'))
        resp.last_modified = mtime

        if has_timestamp():
            if cache_timeout() is not None:
                resp.cache_control.max_age = cache_timeout()
                resp.expires = int(time() + cache_timeout())

        return resp

    @app.route('/about')
    def about():
        return render_layout('about.html')

    @app.route('/raw/<md5>', methods=['GET'])
    def raw(md5):
        en = store.Entry.get_bi_md5(md5)
        if not en:
            abort(404)
        uri = en.image_url
        r = _fetch(uri)
        headers = {k: r.headers[k] for k in (
            'expires',
            'date',
            'cache-control',
            'content-type',
            'content-length',
            'accept-ranges',
            'last-modified',
            'connection'
        ) if k in r.headers}
        return r.data, 200, headers

    @app.route('/thumbnail/<md5>', methods=['GET'])
    @timestamped('.thumbnail')
    def thumbnail(md5):
        try:
            if (
                has_timestamp() and
                not expired_request(core.thumbnail_mtime_bi_md5(md5))
            ):
                return Response(status=304)
        except:
            pass

        width = int(request.args['width'])
        content = core.thumbnail_bi_md5(md5, width)
        resp = Response(content, mimetype='image/' + img.kind(data=content))
        resp.content_md5 = calcmd5(content)
        resp.last_modified = core.thumbnail_mtime_bi_md5(md5)

        if has_timestamp():
            cache_timeout = core.thumbnail_cache_timeout_bi_md5(md5)
            if cache_timeout is not None:
                resp.cache_control.max_age = cache_timeout
                resp.expires = int(time() + cache_timeout)

        return resp

    def page_ext(id):
        r = slice(g.per * id, g.per * (id + 1), 1)

        if request.args and 'tags' in request.args:
            tags = request.args['tags'].split(';')
            log.debug('query tags: {}'.format(tags))
            tags = [store.Tag.escape_name(tag) for tag in tags if tag]
        else:
            tags = []

        return store.Entry.get_bi_tags_order_bi_ctime(
            tags=tags,
            r=r,
            safe=not authed()
        )

    @app.route('/page/<int:id>', methods=['GET'])
    @timed
    def main_page(id):
        res = {}
        for art in page_ext(id):
            res[art.md5] = render_template('art.html', art=art)
        return jsonify({'result': res})

    @app.route('/plused/page/<int:id>', methods=['GET'])
    @timed
    def plused_page(id):
        user = get_user_bi_someid()
        r = slice(g.per * id, g.per * (id + 1), 1)
        res = {}
        for art in user.get_plused(r):
            res[art.md5] = render_template('art.html', art=art)
        return jsonify({'result': res})

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

    def authed():
        return try_get_user_bi_someid() is not None

    @app.route('/thumbnail/link/<md5>', methods=['GET'])
    @timestamped('.thumbnail_link')
    def thumbnail_link(md5):
        width = int(request.args['width'])

        link = core.thumbnail_linkout(md5, width)
        if link is None:
            link = url_for('.thumbnail', md5=md5, width=width)

        return enable_timestamp(jsonify(dict(result=link)))

    def enable_timestamp(resp):
        resp.content_md5 = calcmd5(resp.data)
        return expire_based_on_timestamp(resp)

    def expire_based_on_timestamp(resp):
        if has_timestamp():
            if cache_timeout() is not None:
                resp.cache_control.max_age = cache_timeout()
                resp.expires = int(time() + cache_timeout())
        return resp

    @app.route('/test/log', methods=['GET'])
    def test_log():
        work.nonblock(tasks.test_log)
        return jsonify({})

    def cache_timeout():
        return current_app.config.get('AIP_TIMESTAMPED_TIMEOUT', None)

    def not_exist_resp():
        resp = jsonify({
            'error': {
                'message': 'not exist'
            }
        })
        resp.status_code = 404
        return resp

    @app.route('/art/<md5>', methods=['GET'])
    def art(md5):
        art = core.art_bi_md5(md5)
        if art is None:
            return not_exist_resp()

        return jsonify({
            'result': {key: getattr(art, key) for key in [
                'id',
                'md5',
                'width',
                'height',
            ]}
        })

    def bad_arg_resp():
        return jsonify({
            'error': {
                'message': 'bad arg'
            }
        })

    @app.route('/arts', methods=['GET'])
    @timed
    def arts():
        try:
            q = json.loads(request.args['q'])
            assert_in('md5', q)
            assert_is(type(q['md5']), list)
        except:
            log.exception('bad arg: {}', request.args.get('q'))
            return bad_arg_resp()

        res = {}
        for md5 in q['md5']:
            try:
                res[md5] = render_template(
                    'art.html',
                    art=core.art_bi_md5(md5)
                )
            except:
                pass
        return jsonify({'result': res})

    @app.route('/art/detail/part/<md5>', methods=['GET'])
    @timed
    def art_detail_part(md5):
        art = core.art_bi_md5(md5)
        if art is None:
            return not_exist_resp()

        return jsonify({
            'result': render_template(
                'detail.html',
                art=art
            )
        })
