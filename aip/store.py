#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, desc
from hashlib import md5
from functools import partial
from datetime import datetime


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

        id = db.Column(db.Unicode(128), primary_key=True)
        value = db.Column(db.LargeBinary)

    class Plus(db.Model):

        user_id = db.Column(db.Unicode(128), db.ForeignKey('user.id'), primary_key=True)
        entry_id = db.Column(db.Unicode(128), db.ForeignKey('entry.id'), primary_key=True)
        ctime = db.Column(db.DateTime, default=datetime.utcnow)

    @stored
    class Openid(db.Model):

        uri = db.Column(db.UnicodeText, primary_key=True)
        user_id = db.Column(db.Unicode(128), db.ForeignKey('user.id'), index=True)

        @classmethod
        def exists(cls, uri):
            return db.session.query(db.exists().where(cls.uri == uri)).scalar()

    @stored
    class User(db.Model):

        id = db.Column(db.Unicode(128), primary_key=True)
        openids = db.relationship(Openid, lazy=False)
        name = db.Column(db.Unicode(128), unique=True, index=True)
        email = db.Column(db.Unicode(256), unique=True, index=True)
        ctime = db.Column(db.DateTime, default=datetime.utcnow)
        plused = db.relationship('Plus', backref=db.backref('user', lazy=False))

        @property
        def primary_openid(self):
            return self.openids[0]

        @property
        def plused_entries(self):
            from operator import attrgetter as attr
            return [p.entry for p in sorted(self.plused, key=attr('ctime'), reverse=True)]

        def plus(self, entry):
            if entry not in [p.entry for p in self.plused]:
                self.plused.append(Plus(entry=entry))
            db.session.commit()

        def minus(self, entry):
            for p in self.plused:
                if p.entry == entry:
                    db.session.delete(p)
                    break
            db.session.commit()

        def has_plused(self, entry):
            return db.session.query(db.exists().where(and_(
                Plus.user_id == self.id,
                Plus.entry_id == entry.id
            ))).scalar()

        @classmethod
        def get_bi_email(cls, email):
            return cls.query.filter_by(email=email).first()

        @classmethod
        def group_openid(cls, primary, secondary):
            db.session.execute(Openid.__table__.insert({
                'uri': secondary,
                'user_id': db.select([Openid.user_id]).where(Openid.uri == primary)
            }))

    @stored
    class Entry(db.Model):

        id = db.Column(db.Unicode(128), primary_key=True)
        posts = db.relationship('Post', lazy=False)
        plused = db.relationship('Plus', lazy=False, backref=db.backref('entry'))

        @classmethod
        def __declare_last__(cls):
            cls.best_post = property(lambda self: max(self.posts, key=lambda p: p.score))
            for key in ('post_url', 'preview_url', 'height', 'width', 'score'):
                setattr(cls, key, property(partial(lambda key, self: getattr(self.best_post, key), key)))

            cls.ctime = db.column_property(
                db.select([func.min(Post.ctime)]).where(Post.md5 == cls.id)
            )

        @property
        def plus_count(self):
            return len(self.plused)

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

        id = db.Column(db.Unicode(128), primary_key=True)
        image_url = db.Column(db.UnicodeText)
        width = db.Column(db.Integer)
        height = db.Column(db.Integer)
        rating = db.Column(db.Unicode(128))
        score = db.Column(db.Float)
        preview_url = db.Column(db.UnicodeText)
        sample_url = db.Column(db.UnicodeText)
        tags = db.Column(db.UnicodeText)
        ctime = db.Column(db.DateTime)
        mtime = db.Column(db.DateTime)
        site_id = db.Column(db.Unicode(128), index=True)
        post_id = db.Column(db.Unicode(128))
        post_url = db.Column(db.UnicodeText)
        md5 = db.Column(db.Unicode(128), db.ForeignKey('entry.id'), index=True)

    @stored
    class Imgur(db.Model):

        md5 = db.Column(db.Unicode(128), primary_key=True)
        id = db.Column(db.Unicode(16))
        deletehash = db.Column(db.Unicode(32))
        link = db.Column(db.UnicodeText)
        ctime = db.Column(db.DateTime, default=datetime.utcnow)

    @stored
    class Immio(db.Model):

        md5 = db.Column(db.Unicode(128), primary_key=True)
        uid = db.Column(db.Unicode(16))
        uri = db.Column(db.UnicodeText)
        width = db.Column(db.Integer)
        height = db.Column(db.Integer)
        ctime = db.Column(db.DateTime, default=datetime.utcnow)

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
        return User.query.filter_by(id=id).first()

    @stored
    def add_user(user):
        if user.id is None:
            m = md5()
            m.update(_random_name().encode('ascii'))
            user.id = m.hexdigest()
        db.session.add(user)
        db.session.commit()

    @stored
    def get_user_bi_openid(openid):
        return User.query.join(Openid).filter(Openid.uri == openid).first()

    @stored
    def clear():
        db.drop_all()
        db.create_all()

    @stored
    def get_imgur_bi_md5(md5):
        return Imgur.query.get(md5)

    @stored
    def get_immio_bi_md5(md5):
        return Immio.query.get(md5)

    def _pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('PRAGMA cache_size = 100000')

    from sqlalchemy import event
    event.listen(db.engine, 'connect', _pragma_on_connect)

    db.create_all()

    store.db = db
    return store
