#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, desc
from sqlalchemy.orm.exc import NoResultFound
from functools import partial, wraps
from datetime import datetime
import threading
import pickle
from contextlib import contextmanager
from sqlalchemy.orm.query import Query
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy.orm.util import identity_key
from fn.iters import chain
from .sources import sources
import requests
from . import img
from .imfs.utils import thumbnail
from sqlalchemy import inspect


def _scalar_all(self):
    """Same as scalar, but all() instead of one()

    Example:
    ids = Session.query(User.id).filter(User.username.in_(["joe", "sam"])).scalar_all()
    """
    try:
        return [ret if not isinstance(ret, tuple) else ret[0] for ret in self.all()]
    except orm_exc.NoResultFound:
        return []


Query.scalar_all = _scalar_all


def make_imfs(app):
    from .imfs.baidupcs import BaiduPCS
    from .imfs.fs import FS
    from .imfs.cascade import Cascade
    from .imfs.asyncsave import asyncsave
    import os
    return Cascade(
        FS(root=os.path.join(app.config['AIP_TEMP_PATH'], 'imfs')),
        asyncsave(BaiduPCS(app.config['AIP_BAIDUPCS_ACCESS_TOKEN']))
    )


def make(app, create=False):
    db = SQLAlchemy(app)

    class Store(object):

        @property
        def session(self):
            return db.session

    store = Store()
    imfs = make_imfs(app)

    def stored(f):
        setattr(store, f.__name__, f)
        return f

    def flushed(f):
        @wraps(f)
        def inner(*args, **kargs):
            db.session.flush()
            return f(*args, **kargs)
        return inner

    @contextmanager
    def make_session():
        s = db.create_scoped_session()
        try:
            yield s
        finally:
            s.remove()

    @stored
    class Meta(db.Model):

        id = db.Column(db.Unicode(128), primary_key=True)
        value = db.Column(db.LargeBinary)

    class Plus(db.Model):

        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
        entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'), primary_key=True)
        ctime = db.Column(db.DateTime, default=datetime.utcnow)

    @stored
    class Openid(db.Model):

        uri = db.Column(db.UnicodeText, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

        @classmethod
        def exists(cls, uri):
            return db.session.query(db.exists().where(cls.uri == uri)).scalar()

    @stored
    class User(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        openids = db.relationship(Openid, lazy=False)
        name = db.Column(db.Unicode(128), unique=True, index=True)
        email = db.Column(db.Unicode(256), unique=True, index=True)
        ctime = db.Column(db.DateTime, default=datetime.utcnow)
        plused = db.relationship('Plus', backref=db.backref('user'))

        @property
        def primary_openid(self):
            return self.openids[0]

        @property
        def plused_entries(self):
            from operator import attrgetter as attr
            return [p.entry for p in sorted(self.plused, key=attr('ctime'), reverse=True)]

        def get_plused(self, r):
            return Entry.query.join(Plus).filter(Plus.user_id == self.id).order_by(Plus.ctime.desc())[r]

        def plus(self, entry):
            if entry not in [p.entry for p in self.plused]:
                self.plused.append(Plus(entry=entry))

        def minus(self, entry):
            for p in self.plused:
                if p.entry == entry:
                    db.session.delete(p)
                    break

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

    class Tagged(db.Model):

        post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
        tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True, index=True)
        entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'), index=True)

    def valid_size(width, height):
        return width > 0 and height > 0

    def valid_size_post(post):
        return valid_size(post.width, post.height)

    @stored
    class Entry(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        md5 = db.Column(db.Unicode(128), unique=True, index=True)
        ctime = db.Column(db.DateTime, index=True)
        posts = db.relationship('Post', backref=db.backref('entry'))
        plused = db.relationship('Plus', backref=db.backref('entry'))
        tags = db.relationship('Tag', secondary=Tagged.__table__, backref=db.backref('entries'))

        @classmethod
        def __declare_last__(cls):
            cls.best_post = property(lambda self: max(self.posts, key=lambda p: p.score))
            for key in ('post_url', 'preview_url', 'image_url', 'sample_url', 'score'):
                setattr(cls, key, property(partial(lambda key, self: getattr(self.best_post, key), key)))

        @property
        def plus_count(self):
            session = inspect(self).session
            return session.scalar(
                db.select([db.func.count('*')])
                .select_from(table(Plus))
                .where(Plus.entry_id == self.id)
            )

        def _select_valid_size_post(self):
            if valid_size_post(self.best_post):
                return self.best_post
            for post in self.posts:
                if valie_size_post(post):
                    return post

        def _cache_size(self):
            post = self._select_valid_size_post()
            if post is None:
                raise Exception('all posts of %s wrong size' % self.md5)
            self._width = post.width
            self._height = post.height

        @property
        def width(self):
            if not hasattr(self, '_width'):
                self._cache_size()
            return self._width

        @property
        def height(self):
            if not hasattr(self, '_height'):
                self._cache_size()
            return self._height

        @property
        def preview_url_ssl(self):
            return self.source.try_use_ssl(self.preview_url)

        @property
        def source(self):
            for s in sources.values():
                if s.contains(self.post_url):
                    return s
            raise Exception('no match source for %s' % self.post_url)

        @property
        def preview_width(self):
            return self.ideal_width

        @property
        def preview_height(self):
            return int(self.ideal_width * self.height / self.width)

        @classmethod
        @flushed
        def get_bi_md5(self, md5):
            return Entry.query.filter_by(md5=md5).first()

        @classmethod
        def get_or_add_bi_md5(cls, md5, ctime=datetime.utcnow()):
            try:
                db.session.flush()
                return cls.query.filter_by(md5=md5).one()
            except NoResultFound:
                inst = cls(md5=md5, ctime=ctime)
                db.session.add(inst)
                db.session.flush()
                db.session.expire(inst, ['id'])
                return inst

        @classmethod
        def get_bi_tags_order_bi_ctime(cls, tags, r, safe=True):
            db.session.flush()

            q = Entry.query

            if tags:
                qe1 = table(Entry).alias()
                qtid = db.aliased(
                    db.select([Tag.id])
                    .where(Tag.name.in_(tags))
                    .correlate()
                )
                qeid1 = db.aliased(
                    db.select([Tagged.entry_id, Tagged.tag_id])
                    .select_from(db.join(
                        Tagged,
                        qtid,
                        Tagged.tag_id == qtid.c.id
                    ))
                )
                qeid = (
                    db.select([qe1.c.id])
                    .select_from(db.join(
                        qe1,
                        qeid1,
                        qe1.c.id == qeid1.c.entry_id
                    ))
                )

                if safe:
                    qp1 = table(Post).alias()
                    qeid = (
                        qeid
                        .where(db.not_(db.exists(
                            db.select('*')
                            .select_from(qp1)
                            .where(db.and_(
                                db.not_(qp1.c.rating.in_(['s', 'safe'])),
                                qp1.c.entry_id == qe1.c.id
                            ))
                            .correlate(qe1)
                        )))
                    )

                qeid = db.aliased(
                    qeid
                    .group_by(qe1.c.id)
                    .having(
                        func.count(db.distinct(qeid1.c.tag_id)) == len(tags)
                    )
                    .order_by(db.desc(qe1.c.ctime))
                    .limit(r.stop - r.start)
                    .offset(r.start)
                )

                q = (
                    q
                    .join(qeid, Entry.id == qeid.c.id)
                    .options(db.joinedload(Entry.posts, inner=True))
                    #.options(db.joinedload(Entry.plused))
                    #.options(db.joinedload(Entry.tags))
                    .order_by(Entry.ctime.desc())
                )
            else:
                if safe:
                    q = q.filter(db.not_(db.exists(
                        db.select('*')
                        .select_from(Post.__table__)
                        .where(db.and_(db.not_(Post.rating.in_(['s', 'safe'])), Post.entry_id == Entry.id))
                        .correlate(Entry)
                    )))
                q = (
                    q
                    .options(db.joinedload(Entry.posts, inner=True))
                    .order_by(Entry.ctime.desc())[r]
                )

            return q

        def thumbnail(self, width):
            height = int(self.height * width / self.width)
            data = imfs.thumbnail(self.md5, width, height)
            if data is None:
                data = thumbnail(self.data, self.kind, width, height)
                if data is None:
                    raise Exception('get thumbnail of %s failed' % self.md5)
            else:
                self._kind = img.kind(data=data)
            return data

        @property
        def data(self):
            if not hasattr(self, '_data'):
                data = imfs.load(self.md5)
                if data is None:
                    for post in self.posts:
                        try:
                            r = requests.get(post.image_url)
                            if r.ok:
                                data = r.content
                                break
                        except:
                            pass
                    else:
                        raise Exception('get data of %s failed' % self.md5)
                    imfs.save(self.md5, data)
                self._data = data
            return self._data

        @property
        def kind(self):
            if not hasattr(self, '_kind'):
                self._kind = img.kind(data=self.data)
            return self._kind

    @stored
    def table(cls):
        return cls.__table__

    @stored
    class Post(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        image_url = db.Column(db.UnicodeText)
        width = db.Column(db.Integer)
        height = db.Column(db.Integer)
        rating = db.Column(db.Unicode(16))
        score = db.Column(db.Float)
        preview_url = db.Column(db.UnicodeText)
        sample_url = db.Column(db.UnicodeText)
        ctime = db.Column(db.DateTime, index=True)
        post_url = db.Column(db.UnicodeText, unique=True, index=True)
        entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'), index=True)
        tags = db.relationship('Tag', secondary=Tagged.__table__)

        @property
        def md5(self):
            return self.entry.md5

        def from_dict(self, d):
            for key, value in d.items():
                if hasattr(self, key):
                    try:
                        setattr(self, key, value)
                    except:
                        # for md5 field
                        pass

        @classmethod
        @flushed
        def put(cls, **kargs):
            entry = Entry.get_or_add_bi_md5(md5=kargs['md5'], ctime=kargs['ctime'])

            tags = [Tag.get_or_add_bi_name(name) for name in set(kargs['tags'])]
            del kargs['tags']

            try:
                post = cls.query.filter_by(post_url=kargs['post_url']).options(db.joinedload(cls.entry)).one()
                if post.entry.md5 != kargs['md5']:
                    raise Exception('md5 changed %s -> %s' % (post.md5, kargs['md5']))
                post.from_dict(kargs)
            except NoResultFound:
                post = cls(entry=entry)
                post.from_dict(kargs)
                db.session.add(post)
                db.session.flush()
                db.session.expire(post, ['id'])

            for tag in tags:
                db.session.merge(Tagged(post_id=post.id, tag_id=tag.id, entry_id=entry.id))

        @classmethod
        @flushed
        def puts(cls, posts):
            posts = list(posts)
            tagnames = set(chain.from_iterable([post['tags'] for post in posts]))
            tags = {name: Tag.get_or_add_bi_name(name) for name in tagnames}

            def inner(posts):
                for kargs in posts:
                    entry = Entry.get_or_add_bi_md5(md5=kargs['md5'], ctime=kargs['ctime'])
                    kargs = {k: v for k, v in kargs.items() if k != 'tags'}
                    try:
                        post = cls.query.filter_by(post_url=kargs['post_url']).options(db.joinedload(cls.entry)).one()
                        if post.entry.md5 != kargs['md5']:
                            raise Exception('md5 changed %s -> %s' % (post.md5, kargs['md5']))
                        post.from_dict(kargs)
                    except NoResultFound:
                        post = cls(entry=entry)
                        post.from_dict(kargs)
                        db.session.add(post)
                    yield post

            flushed = False
            seen = set()
            for kargs, post in zip(posts, list(inner(posts))):
                if post.id is None:
                    if not flushed:
                        db.session.flush()
                        flushed = True
                    db.session.expire(post, ['id'])
                else:
                    if post.id in seen:
                        continue
                    seen.add(post.id)
                for name in set(kargs['tags']):
                    tag = tags[name]
                    db.session.merge(Tagged(post_id=post.id, tag_id=tag.id, entry_id=post.entry.id))

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

    @stored
    class Tag(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.UnicodeText, unique=True, index=True)
        lock = threading.RLock()

        @property
        def short_name(self):
            n = app.config['AIP_TAG_SHORT_NAME_LIMIT']
            return self.name if len(self.name) <= n else self.name[:n - 3] + '...'

        @property
        def display_name(self):
            return self.name.replace('_', ' ')

        @classmethod
        def escape_name(cls, name):
            return name.replace(' ', '_')

        def locked(f):
            @wraps(f)
            def inner(self, *args, **kargs):
                with self.lock:
                    return f(self, *args, **kargs)
            return inner

        @classmethod
        @locked
        def add(cls, tag):
            # http://stackoverflow.com/a/5083472
            db.session.add(tag)
            db.session.flush()
            db.session.refresh(tag, ['id'])
            #logging.debug('new tag (%d, %s)' % (tag.id, tag.name))
            return tag

        @classmethod
        def get_or_add_bi_name(cls, name):
            try:
                db.session.flush()
                return cls.query.filter_by(name=name).one()
            except NoResultFound:
                inst = cls(name=name)
                cls.add(inst)
                db.session.flush()
                db.session.expire(inst, ['id'])
                return inst

        @classmethod
        @locked
        def remove(cls, id):
            db.session.execute(db.delete(cls.__table__, db.where(cls.id == id)))

    def _random_name():
        import uuid
        return str(uuid.uuid4())

    @stored
    @flushed
    def put(o):
        o = db.session.merge(o)

    @stored
    @flushed
    def get_entry_bi_id(id):
        return Entry.query.get(id)

    @stored
    @flushed
    def get_entries_order_bi_ctime(r=None):
        q = Entry.query.order_by(desc(Entry.ctime))
        return q if r is None else q[r]

    @stored
    @flushed
    def latest_ctime_bi_site_id(id):
        return db.session.query(func.max(Post.ctime)).scalar()

    @stored
    @flushed
    def image_count():
        return db.session.query(func.count(Post.id)).scalar()

    @stored
    @flushed
    def user_count():
        return db.session.query(func.count(User.id)).scalar()

    @stored
    @flushed
    def unique_image_count():
        return Post.query.group_by(Post.entry_id).count()

    @stored
    @flushed
    def entry_count():
        return db.session.query(func.count(Entry.id)).scalar()

    @stored
    def set_meta(id, value):
        put(Meta(id=id, value=value))

    @stored
    @flushed
    def get_meta(id):
        meta = Meta.query.get(id)
        return meta.value if meta else None

    @stored
    @flushed
    def get_user_bi_id(id):
        return User.query.filter_by(id=id).first()

    @stored
    @flushed
    def add_user(name, email, openid):
        user = store.User(name=name, email=email)
        user.openids.append(store.Openid(uri=openid))
        db.session.add(user)
        db.session.flush()
        db.session.expire(user, ['id'])
        return user

    @stored
    @flushed
    def get_user_bi_openid(openid):
        return User.query.join(Openid).filter(Openid.uri == openid).first()

    @stored
    @flushed
    def clear():
        db.drop_all()
        db.create_all()

    @stored
    @flushed
    def get_imgur_bi_md5(md5):
        return Imgur.query.get(md5)

    @stored
    def imgur_bi_md5(md5):
        with make_session() as session:
            return session.query(Imgur).get(md5)

    @stored
    @flushed
    def get_immio_bi_md5(md5):
        return Immio.query.get(md5)

    @stored
    @flushed
    def plus(user_id, entry_id):
        db.session.merge(Plus(user_id=user_id, entry_id=entry_id))

    @stored
    @flushed
    def minus(user_id, entry_id):
        Plus.query.filter_by(user_id=user_id, entry_id=entry_id).delete()

    @stored
    @flushed
    def plus_count(entry_id):
        return db.session.scalar(
            db.select([db.func.count('*')])
            .select_from(Plus.__table__)
            .where(Plus.entry_id == entry_id)
        )

    @stored
    def get_entry_bi_md5(md5):
        return Entry.get_bi_md5(md5)

    @stored
    def thumbnail_mtime_bi_md5(md5):
        return imfs.mtime(md5)

    @stored
    def thumbnail_cache_timeout_bi_md5(md5):
        return imfs.cache_timeout(md5)

    @stored
    def thumbnail_bi_md5(md5, width):
        with make_session() as session:
            en = (
                session.query(Entry)
                .filter_by(md5=md5)
                .options(db.joinedload(Entry.posts, inner=True))
                .first()
            )
        return en.thumbnail(width)

    def sessioned(f):
        @wraps(f)
        def inner(*args, **kargs):
            if 'session' not in kargs:
                kargs['session'] = db.session
            return f(*args, **kargs)
        return inner

    @stored
    @sessioned
    def art_bi_md5(md5, session):
        return (
            session.query(Entry)
            .filter_by(md5=md5)
            .first()
        )

    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        optimize_sqlite(db)

    if create:
        db.create_all()

    db.configure_mappers()

    store.db = db
    return store


def optimize_sqlite(db):
    def _pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('PRAGMA cache_size = 100000')

    from sqlalchemy import event
    event.listen(db.engine, 'connect', _pragma_on_connect)
