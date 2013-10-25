#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import re
from flask import (
    g,
    session,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    render_template,
    abort,
    Response
)
from operator import attrgetter as attr
from io import BytesIO
from PIL import Image
from collections import namedtuple
from urllib.parse import urlparse, urlunparse
from .layout import render_layout
from functools import wraps
from .log import Log
from time import time


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


def _fetch_image(url):
    try:
        logging.info('fetch image: %s' % url)
        r = _fetch(url)
        return r.data
    except Exception as e:
        logging.error('fetch image failed: %s' % url)
        logging.exception(e)
        return None


def make(app, oid, cached, store):

    from .momentjs import momentjs
    app.jinja_env.globals['momentjs'] = momentjs

    def timed(f):
        @wraps(f)
        def inner(*args, **kargs):
            try:
                start = time()
                return f(*args, **kargs)
            finally:
                log.info('%s take %.4f' % (f.__name__, time() - start))
        return inner

    @prop
    def last_update_time(self):
        return store.get_meta('last_update_time')

    @prop
    def entry_count(self):
        return store.entry_count()

    @prop
    def user_count(self):
        return store.user_count()

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
            logging.info('openid %s already in session' % session['openid'])
            if store.Openid.exists(resp.identity_url):
                logging.info('group openid %s with %s' % (resp.identity_url, session['openid']))
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
        return render_layout('create_profile.html', next_url=oid.get_next_url())

    @app.route('/logout')
    def logout():
        session.pop('openid', None)
        flash('You were signed out')
        return redirect(oid.get_next_url())

    @app.route('/sample/<md5>')
    @cached(timeout=24 * 60 * 60)
    def sample(md5):
        im = store.get_image_bi_md5(md5)
        url = im.sample_url if im.sample_url else im.image_url
        height = im.height
        input_stream = BytesIO(_fetch_image(url))
        im = Image.open(input_stream)
        im.thumbnail((g.sample_width, height), Image.ANTIALIAS)
        output_stream = BytesIO()
        im.save(output_stream, format='JPEG')
        return output_stream.getvalue(), 200, {'Content-Type': 'image/jpeg'}

    @app.route('/')
    def posts():
        tags = request.args.get('q', '')
        return render_layout('index.html', tags=tags)

    @app.route('/plused')
    def plused():
        return render_layout('plused.html')

    @app.route('/style.css')
    #@cached(timeout=24 * 60 * 60)
    def style():
        import scss
        from collections import OrderedDict
        root = os.path.join(app.static_folder, 'scss')
        c = scss.Scss(
            scss_vars={},
            scss_opts={
                'compress': True,
                'debug_info': True,
                'load_paths': [root]
            }
        )
        sources = []
        for filename in os.listdir(root):
            if re.match(r'aip-\w+\.scss', filename):
                with open(os.path.join(root, filename), 'rb') as f:
                    content = f.read().decode('utf-8')
                sources.append((filename, content))
        c._scss_files = OrderedDict(sources)
        return c.compile(), 200, {'Content-Type': 'text/css'}

    @app.route('/js')
    def js():
        return (
            render_template('base.js'),
            200,
            {'Content-Type': 'text/javascript'}
        )

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

    @app.route('/thumbnail/<md5>/<int:width>', methods=['GET'])
    def thumbnail(md5, width):
        try:
            if request.headers.get('if-modified-since') == store.thumbnail_mtime_bi_md5(md5).ctime():
                return Response(status=304)
        except:
            pass

        en = store.get_entry_bi_md5(md5)
        resp = Response(en.thumbnail(width), mimetype='image/' + en.kind)
        resp.headers['last-modified'] = store.thumbnail_mtime_bi_md5(md5).ctime()
        cache_timeout = store.thumbnail_cache_timeout_bi_md5(md5)

        if cache_timeout is not None:
            resp.cache_control.max_age = cache_timeout
            resp.expires = int(time() + cache_timeout)

        return resp

    def page_ext(id):
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

    @app.route('/page/<int:id>', methods=['GET'])
    @timed
    def main_page(id):
        return render_layout('page.html', entries=page_ext(id))

    @app.route('/plused/page/<int:id>', methods=['GET'])
    @timed
    def plused_page(id):
        user = get_user_bi_someid()
        r = slice(g.per * id, g.per * (id + 1), 1)
        return render_layout('page.html', entries=user.get_plused(r))

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
