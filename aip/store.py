#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, desc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from hashlib import md5


def make(app):
    db = SQLAlchemy(app)

    class Store(object):
        pass

    store = Store()

    def stored(f):
        setattr(store, f.__name__, f)
        return f

    @stored
    class Meta(db.Model):

        id = db.Column(db.String(128), primary_key=True)
        value = db.Column(db.LargeBinary)

    plus_table = db.Table(
        'plus',
        db.Model.metadata,
        db.Column('user_id', db.LargeBinary(128), db.ForeignKey('user.id')),
        db.Column('entry_id', db.LargeBinary(128), db.ForeignKey('entry.id'))
    )

    @stored
    class User(db.Model):

        id = db.Column(db.LargeBinary(128), primary_key=True)
        openid = db.Column(db.Text, unique=True, index=True)
        name = db.Column(db.String(128), unique=True, index=True)
        email = db.Column(db.String(256), unique=True, index=True)
        plused = db.relationship('Entry', secondary=plus_table, backref='plused')

        def plus(self, entry):
            self.plused.append(entry)

        def minus(self, entry):
            self.plused.remove(entry)

        def has_plused(self, entry):
            return Entry.query.filter_by(id=entry.id).with_parent(self, 'plused').count() > 0

    @stored
    class Entry(db.Model):

        id = db.Column(db.LargeBinary(128), primary_key=True)

        @classmethod
        def __declare_last__(cls):
            sub = db.session.query(
                Post.id,
                func.max(Post.score).label('score'),
            ).group_by(Post.md5).subquery()
            cls.best_post_id = db.column_property(
                db.select([Post.id]).where((Post.id == sub.c.id) & (Post.md5 == cls.id))
            )
            cls.best_post = db.relationship(
                Post,
                primaryjoin=cls.best_post_id == Post.id,
                foreign_keys=cls.best_post_id,
                viewonly=True,
                uselist=False,
                lazy=False
            )
            for key in ('post_url', 'preview_url', 'height', 'width', 'score'):
                setattr(cls, key, property(lambda self: getattr(self.best_post, key)))

            cls.plus_count = db.column_property(
                db.select([func.count('*')]).where(plus_table.c.entry_id == cls.id)
            )
            cls.ctime = db.column_property(
                db.select([func.min(Post.ctime)]).where(Post.md5 == cls.id)
            )

        @property
        def preview_width(self):
            return self.ideal_width

        @property
        def preview_height(self):
            return int(self.ideal_width * self.height / self.width)

        @property
        def md5(self):
            return self.id

    @stored
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
        site_id = db.Column(db.String(128), index=True)
        post_id = db.Column(db.String(128))
        post_url = db.Column(db.Text)
        md5 = db.Column(db.LargeBinary(128), db.ForeignKey('entry.id'), index=True)

    def _random_name():
        import uuid
        return str(uuid.uuid4())

    @stored
    def put(o):
        if o.id is None:
            o.id = _random_name()
        o = db.session.merge(o)
        db.session.add(o)

    @stored
    def get_entry_bi_id(id):
        if type(id) is str:
            id = id.encode('utf-8')
        return Entry.query.filter_by(id=id).first()

    @stored
    def put_image(im):
        if im.id is None:
            im.id = _random_name()

        origin = Post.query.filter_by(site_id=im.site_id, post_id=im.post_id).first()
        if origin is not None:
            im.id = origin.id
            im = db.session.merge(im)
        db.session.add(im)

        # add entry
        entry = get_entry_bi_id(im.md5)
        if entry is None:
            entry = Entry(id=im.md5)
            db.session.add(entry)

    @stored
    def get_images_order_bi_ctime(r=None):
        q = Post.query.order_by(Post.ctime.desc())
        return q if r is None else q[r]

    @stored
    def get_entries_order_bi_ctime(r=None):
        q = Entry.query.order_by(desc(Entry.ctime))
        return q if r is None else q[r]

    @stored
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

    @stored
    def latest_ctime_bi_site_id(id):
        return db.session.query(func.max(Post.ctime)).first()[0]

    @stored
    def image_count():
        return db.session.query(func.count(Post.id)).first()[0]

    @stored
    def user_count():
        return db.session.query(func.count(User.id)).first()[0]

    @stored
    def unique_image_count():
        return Post.query.group_by(Post.md5).count()

    @stored
    def entry_count():
        return db.session.query(func.count(Entry.id)).first()[0]

    @stored
    def set_meta(id, value):
        put(Meta(id=id, value=value))

    @stored
    def get_meta(id):
        return Meta.query.filter_by(id=id).first()

    @stored
    def get_image_bi_md5(md5):
        return Post.query.filter_by(md5=md5).first()

    @stored
    def get_user_bi_id(id):
        if type(id) is str:
            id = id.encode('utf-8')
        return User.query.filter_by(id=id).first()

    @stored
    def add_user(user):
        if user.id is None:
            assert user.openid is not None
            m = md5()
            m.update(user.openid.encode('utf-8'))
            user.id = m.hexdigest().encode('ascii')
        db.session.add(user)
        db.session.commit()

    @stored
    def get_user_bi_openid(openid):
        m = md5()
        m.update(openid.encode('utf-8'))
        return get_user_bi_id(m.hexdigest().encode('ascii'))

    @stored
    def clear():
        db.drop_all()
        db.create_all()

    def _pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('PRAGMA cache_size = 100000')

    from sqlalchemy import event
    event.listen(db.engine, 'connect', _pragma_on_connect)

    db.create_all()

    store.db = db
    return store
