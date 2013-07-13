#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_
from hashlib import md5


db = SQLAlchemy()


class Meta(db.Model):

    id = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.LargeBinary)


class User(db.Model):

    id = db.Column(db.LargeBinary(128), primary_key=True)
    openid = db.Column(db.Text, unique=True)
    name = db.Column(db.String(128), unique=True)
    email = db.Column(db.String(256), unique=True)


class Entry(db.Model):

    id = db.Column(db.LargeBinary(128), primary_key=True)
    posts = db.relationship('Post')


class Post(db.Model):

    id = db.Column(db.String(128), primary_key=True)
    image_url = db.Column(db.Text)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    rating = db.Column(db.String(128))
    score = db.Column(db.Float)
    preview_url = db.Column(db.Text)
    sample_url = db.Column(db.Text)
    tags = db.Column(db.Text)
    ctime = db.Column(db.DateTime)
    mtime = db.Column(db.DateTime)
    site_id = db.Column(db.String(128))
    post_id = db.Column(db.String(128))
    post_url = db.Column(db.Text)
    md5 = db.Column(db.LargeBinary(128), db.ForeignKey('entry.id'))


def _random_name():
    import uuid
    return str(uuid.uuid4())


def put(o):
    if o.id is None:
        o.id = _random_name()
    o = db.session.merge(o)
    db.session.add(o)


def put_image(im):
    if im.id is None:
        im.id = _random_name()

    origin = Post.query.filter_by(site_id=im.site_id, post_id=im.post_id).first()

    if origin is not None:
        im.id = origin.id
        im = db.session.merge(im)

    db.session.add(im)


def get_images_order_bi_ctime(r=None):
    q = Post.query.order_by(Post.ctime.desc())
    return q if r is None else q[r]


def get_unique_images_order_bi_ctime(r=None):
    sub = db.session.query(
        func.max(Post.score),
        Post.id.label('best_id')
    ).group_by(Post.md5).subquery()
    q = Post.query.join(
        sub,
        and_(Post.id == sub.c.best_id)
    ).order_by(Post.ctime.desc())
    return q if r is None else q[r]


def latest_ctime_bi_site_id(id):
    return db.session.query(func.max(Post.ctime)).first()[0]


def image_count():
    return db.session.query(func.count(Post.id)).first()[0]


def user_count():
    return db.session.query(func.count(User.id)).first()[0]


def unique_image_count():
    return Post.query.group_by(Post.md5).count()


def set_meta(id, value):
    put(Meta(id=id, value=value))


def get_meta(id):
    return Meta.query.filter_by(id=id).first()


def get_image_bi_md5(md5):
    return Post.query.filter_by(md5=md5).first()


def get_user_bi_id(id):
    return User.query.filter_by(id=id).first()


def put_user(user):
    if user.id is None:
        assert user.openid is not None
        m = md5()
        m.update(user.openid.encode('utf-8'))
        user.id = m.hexdigest().encode('ascii')
    return put(user)


def get_user_bi_openid(openid):
    m = md5()
    m.update(openid.encode('utf-8'))
    return get_user_bi_id(m.hexdigest().encode('ascii'))


def clear():
    db.drop_all()
    db.create_all()


def make(app):
    db.app = app
    db.init_app(app)
    db.create_all()
    return db
