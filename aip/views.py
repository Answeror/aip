#!/usr/bin/env python
# -*- coding: utf-8 -*-


from functools import wraps
import logging
import os
import threading
import pickle
from flask import request
from flask import (
    g,
    render_template,
    session,
    redirect,
    url_for,
    flash
)
from operator import attrgetter as attr
from io import BytesIO
from PIL import Image
from collections import namedtuple
from .settings import PER, COLUMN_WIDTH, GUTTER, LOG_FILE_PATH
from . import app, oid


def _url_for_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


Post = namedtuple('Post', (
    'url',
    'preview_url',
    'preview_width',
    'preview_height',
    'md5'
))


def _scale(images):
    images = list(images)
    posts = []
    if images:
        for im in images:
            im.scale = g.column_width
        sm = sorted(images, key=attr('score'), reverse=True)
        for im in sm[:max(1, int(len(sm) / PER))]:
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


lock = threading.RLock()


def locked(f):
    @wraps(f)
    def inner(*args, **kargs):
        with lock:
            return f(*args, **kargs)
    return inner


def prop(f):
    setattr(g.__class__, f.__name__, property(f))


@prop
def store(self):
    if not hasattr(g, '_store'):
        g._store = app.config['aip.store']
    return g._store


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
def repo(self):
    if not hasattr(g, '_repo'):
        g._repo = g.store.repo
    return g._repo


@prop
def sample_width(self):
    from .settings import SAMPLE_WIDTH
    return SAMPLE_WIDTH


@app.before_request
def setup():
    import urllib3
    g.http = urllib3.PoolManager()

    g.session = g.repo.connection()
    g.url_for_page = _url_for_page
    g.column_width = COLUMN_WIDTH
    g.gutter = GUTTER
    g.per = PER


@locked
def update(begin=None):
    from datetime import datetime
    begin = datetime.strptime(begin, '%Y%m%d')
    set_last_update_time(datetime.now())
    update_images(begin)
    return 'updated from %s' % begin.strftime('%Y-%m-%d')


def set_last_update_time(value):
    g.session.set_meta('last_update_time', pickle.dumps(value))
    g.session.commit()


def last_update_time():
    value = g.session.get_meta('last_update_time')
    return '' if value is None else pickle.loads(value).strftime('%Y-%m-%d %H:%M:%S')


def update_images(begin=None, limit=65536):
    for make in g.sources:
        source = make(g.store.Image)
        tags = []
        for i, im in zip(list(range(limit)), source.get_images(tags)):
            if begin is not None and im.ctime <= begin:
                break
            g.session.put_image(im)
        g.session.commit()


def clear():
    g.repo.clear()
    return ''


def fetch(url):
    return g.http.request('GET', url)


def _fetch_image(url):
    try:
        logging.info('fetch image: %s' % url)
        r = fetch(url)
        return r.data
    except Exception as e:
        logging.error('fetch image failed: %s' % url)
        logging.exception(e)
        return None


def sample(md5):
    md5 = md5.encode('ascii')
    im = g.session.get_image_bi_md5(md5)
    url = im.sample_url if im.sample_url else im.url
    height = im.height
    input_stream = BytesIO(_fetch_image(url))
    im = Image.open(input_stream)
    im.thumbnail((g.sample_width, height), Image.ANTIALIAS)
    output_stream = BytesIO()
    im.save(output_stream, format='JPEG')
    return output_stream.getvalue(), 200, {'Content-Type': 'image/jpeg'}


def image_count():
    return str(g.session.image_count())


def user_count():
    return str(g.session.user_count())


def unique_image_count():
    return str(g.session.unique_image_count())


def unique_image_md5():
    return b'\n'.join([im.md5 for im in g.session.get_unique_images_order_bi_ctime()])


def posts(page):
    from .pagination import Infinite
    pagination = Infinite(
        page,
        PER,
        lambda begin, end: _scale(
            g.session.get_unique_images_order_bi_ctime(r=slice(begin, end, 1))
        )
    )
    return render_template('index.html', pagination=pagination)


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
        if filename.endswith('.scss'):
            with open(os.path.join(root, filename), 'rb') as f:
                content = f.read().decode('utf-8')
            sources.append((filename, content))
    c._scss_files = OrderedDict(sources)
    return c.compile(), 200, {'Content-Type': 'text/css'}


def log():
    with open(LOG_FILE_PATH, 'rb') as f:
        return f.read()


@app.before_request
def lookup_current_user():
    g.user = None
    if 'openid' in session:
        g.user = g.session.get_user_bi_openid(session['openid'])


@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    openid = 'https://www.google.com/accounts/o8/id'
    return oid.try_login(
        openid,
        ask_for=['email', 'fullname', 'nickname']
    )


@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    if g.user is not None:
        flash(u'Successfully signed in')
        return redirect(oid.get_next_url())
    return redirect(url_for(
        '.create_profile',
        next=oid.get_next_url(),
        name=resp.fullname or resp.nickname,
        email=resp.email
    ))


def create_profile():
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('.posts'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            g.session.put_user(g.store.User(name=name, email=email, openid=session['openid']))
            g.session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html', next_url=oid.get_next_url())


def logout():
    session.pop('openid', None)
    flash(u'You were signed out')
    return redirect(oid.get_next_url())
