#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import urllib3
from flask import (
    g,
    render_template,
    make_response,
    session,
    redirect,
    request,
    url_for,
    flash
)
from operator import attrgetter as attr
from .settings import PER, LOG_FILE_PATH
import os
from io import BytesIO
from PIL import Image
from collections import namedtuple


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


class Local(object):

    def __init__(self, blue):
        self.blue = blue
        self.http = urllib3.PoolManager()

    @property
    def store(self):
        return self.blue.store

    def fetch(self, url):
        return self.http.request('GET', url)

    def _fetch_image(self, url):
        try:
            logging.info('fetch image: %s' % url)
            r = self.fetch(url)
            return r.data
        except Exception as e:
            logging.error('fetch image failed: %s' % url)
            logging.exception(e)
            return None

    def sample(self, md5):
        md5 = md5.encode('ascii')

        with self.connection() as con:
            im = con.get_image_bi_md5(md5)
            url = im.sample_url if im.sample_url else im.url
            height = im.height

        input_stream = BytesIO(self._fetch_image(url))
        im = Image.open(input_stream)
        im.thumbnail((self.sample_width, height), Image.ANTIALIAS)
        output_stream = BytesIO()
        im.save(output_stream, format='JPEG')
        #return send_file(output_stream, mimetype='image/jpeg')
        return output_stream.getvalue(), 200, {'Content-Type': 'image/jpeg'}

    @property
    def sample_width(self):
        return self.blue.sample_width

    def connection(self):
        return self.blue.connection()

    def image_count(self):
        with self.connection() as con:
            return str(con.image_count())

    def user_count(self):
        return str(self.session.user_count())

    def unique_image_count(self):
        with self.connection() as con:
            return str(con.unique_image_count())

    def unique_image_md5(self):
        with self.connection() as con:
            return b'\n'.join([im.md5 for im in con.get_unique_images_order_bi_ctime()])

    def update_images(self, begin):
        from datetime import datetime
        begin = datetime.strptime(begin, '%Y%m%d')
        self.blue.update_images(begin)
        return ''

    def last_update_time(self):
        t = self.blue.last_update_time
        return '' if t is None else t.strftime('%Y-%m-%d %H:%M:%S')

    def posts_in_page(self, page):
        with self.connection() as con:
            from .pagination import Infinite
            pagination = Infinite(
                page,
                PER,
                lambda begin, end: _scale(
                    con.get_unique_images_order_bi_ctime(r=slice(begin, end, 1))
                )
            )
            for it in pagination.items:
                pass
            return render_template('index.html', pagination=pagination)

    def stream(self, page):
        return make_response(
            self.posts_in_page(page),
            200,
            {'Content-Type': 'application/octet-stream'}
        )

    def update(self, begin):
        from datetime import datetime
        begin = datetime.strptime(begin, '%Y%m%d')
        self.blue.update(begin)
        return 'updated from %s' % begin.strftime('%Y-%m-%d')

    def scss(self):
        import scss
        from collections import OrderedDict
        root = os.path.join(self.blue.static_folder, 'scss')
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

    def log(self):
        with open(LOG_FILE_PATH, 'rb') as f:
            return f.read()

    def clear(self):
        self.blue.clear()
        return ''

    @property
    def session(self):
        return self.connection()

    @property
    def user(self):
        if not hasattr(self, '_user'):
            self._user = None
            if 'openid' in session:
                self._user = self.session.get_user_bi_openid(session['openid'])
        return self._user

    @property
    def oid(self):
        return self.blue.oid

    def login(self):
        if self.user is not None:
            return redirect(self.oid.get_next_url())
        if request.method == 'POST':
            openid = request.form.get('openid')
            if openid:
                return self.oid.try_login(
                    openid,
                    ask_for=['email', 'fullname', 'nickname']
                )
        return render_template(
            'login.html',
            next=self.oid.get_next_url(),
            error=self.oid.fetch_error()
        )

    def create_or_login(self, resp):
        session['openid'] = resp.identity_url
        if self.user is not None:
            flash(u'Successfully signed in')
            return redirect(self.oid.get_next_url())
        return redirect(url_for(
            '.create_profile',
            next=self.oid.get_next_url(),
            name=resp.fullname or resp.nickname,
            email=resp.email
        ))

    def create_profile(self):
        if self.user is not None or 'openid' not in session:
            return redirect(url_for('index'))
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            if not name:
                flash(u'Error: you have to provide a name')
            elif '@' not in email:
                flash(u'Error: you have to enter a valid email address')
            else:
                flash(u'Profile successfully created')
                self.session.put_user(self.store.User(name=name, email=email, openid=session['openid']))
                self.session.commit()
                return redirect(self.oid.get_next_url())
        return render_template('create_profile.html', next_url=self.oid.get_next_url())

    def logout(self):
        session.pop('openid', None)
        flash(u'You were signed out')
        return redirect(self.oid.get_next_url())
