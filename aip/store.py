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
#import logging
from .dag import Dag
from sqlalchemy.orm.query import Query
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy.orm.util import identity_key


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


def make(app):
    db = SQLAlchemy(app)

    class Store(object):
        pass

    store = Store()

    def stored(f):
        setattr(store, f.__name__, f)
        return f

    def flushed(f):
        @wraps(f)
        def inner(*args, **kargs):
            return f(*args, **kargs)
        return inner

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
            db.session.expire(entry, ['plus_count'])

        def minus(self, entry):
            for p in self.plused:
                if p.entry == entry:
                    db.session.delete(p)
                    break
            db.session.expire(entry, ['plus_count'])

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
        tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)
        entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'), index=True)

    @stored
    class Entry(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        md5 = db.Column(db.Unicode(128), unique=True)
        ctime = db.Column(db.DateTime, index=True)
        posts = db.relationship('Post', backref=db.backref('entry'))
        plused = db.relationship('Plus', backref=db.backref('entry'))
        tags = db.relationship('Tag', secondary=Tagged.__table__, backref=db.backref('entries'))

        @classmethod
        def __declare_last__(cls):
            cls.best_post = property(lambda self: max(self.posts, key=lambda p: p.score))
            for key in ('post_url', 'preview_url', 'image_url', 'sample_url', 'height', 'width', 'score'):
                setattr(cls, key, property(partial(lambda key, self: getattr(self.best_post, key), key)))
            cls.plus_count = db.column_property(
                db.select([db.func.count('*')])
                .select_from(Plus.__table__)
                .where(Plus.entry_id == cls.id)
                .correlate(cls.__table__)
                .as_scalar()
            )

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
        def get_bi_tags_order_bi_ctime(cls, tags, r):
            db.session.flush()

            if tags:
                qsub = db.select([Tag.id]).where(Tag.name.in_(tags)).correlate()
                tt = Tagged.__table__.alias()
                qcount = (
                    db.select([db.func.count('*')])
                    .select_from(Tag.__table__)
                    .where(db.and_(Tag.id.in_(qsub), db.exists(
                        db.select('*')
                        .select_from(tt)
                        .where(db.and_(tt.c.entry_id == Entry.id, tt.c.tag_id == Tag.id))
                        .correlate(Entry)
                        .correlate(Tag)
                    ))).as_scalar()
                )
                q = (
                    Entry.query
                    .filter(qcount == len(tags))
                    .order_by(Entry.ctime.desc())
                    .options(db.subqueryload(Entry.posts))
                    .options(db.subqueryload(Entry.plused))
                    .options(db.subqueryload(Entry.tags))
                )
                #logging.debug(str(q))
                q = q[r]
            else:
                q = Entry.query.order_by(Entry.ctime.desc())[r]

            return q

    def dagw(f):
        '''dag for write'''
        @wraps(f)
        def inner(*args, **kargs):
            if 'dag' in kargs and kargs['dag'] is not None:
                return f(*args, **kargs)
            else:
                dag = kargs['dag'] = get_dag()
                ret = f(*args, **kargs)
                set_dag(dag)
                return ret
        return inner

    def dagr(f):
        '''dag for read'''
        @wraps(f)
        def inner(*args, **kargs):
            if 'dag' in kargs and kargs['dag'] is not None:
                kargs['dag'] = get_dag()
            return f(*args, **kargs)
        return inner

    @stored
    @contextmanager
    def autodag():
        dag = get_dag()
        yield dag
        set_dag(dag)

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
        post_url = db.Column(db.UnicodeText)
        entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'), index=True)
        tags = db.relationship('Tag', secondary=Tagged.__table__)

        def from_dict(self, d):
            for key, value in d.items():
                if hasattr(self, key):
                    setattr(self, key, value)

        @classmethod
        @flushed
        @dagw
        def put(cls, dag, **kargs):
            entry = Entry.get_or_add_bi_md5(md5=kargs['md5'], ctime=kargs['ctime'])

            tags = [Tag.get_or_add_bi_name(name, dag=dag) for name in set(kargs['tags'])]
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
    def get_dag():
        data = get_meta(app.config['AIP_META_DAG'])
        return Dag() if data is None else Dag.from_dict(pickle.loads(data))

    @stored
    def set_dag(dag):
        set_meta(app.config['AIP_META_DAG'], pickle.dumps(dag.to_dict()))

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
        @dagw
        def add(cls, tag, dag):
            # http://stackoverflow.com/a/5083472
            db.session.add(tag)
            db.session.flush()
            db.session.refresh(tag, ['id'])
            dag.add(tag.id)
            #logging.debug('new tag (%d, %s)' % (tag.id, tag.name))
            return tag

        @classmethod
        @dagw
        def get_or_add_bi_name(cls, name, dag):
            try:
                db.session.flush()
                return cls.query.filter_by(name=name).one()
            except NoResultFound:
                inst = cls(name=name)
                cls.add(inst, dag=dag)
                db.session.flush()
                db.session.expire(inst, ['id'])
                return inst

        @classmethod
        @locked
        @dagw
        def remove(cls, id, dag):
            db.session.execute(db.delete(cls.__table__, db.where(cls.id == id)))
            dag.remove(id)

        @classmethod
        @locked
        @dagw
        def link(cls, child, parent, dag):
            dag.link(child, parent)

        @classmethod
        @locked
        @dagw
        def unlink(cls, child, parent, dag):
            dag.unlink(child, parent)

        #@classmethod
        #@locked
        #@dagr
        #def entries(cls, ids, dag):
            #down = set().union(*[cls.dag.down[i] for i in ids])
            #return Entry.query.join(Post).join(tagged_table).filter(tagged_table.c.tag_id.in_(list(down))).all()

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
    @flushed
    def get_immio_bi_md5(md5):
        return Immio.query.get(md5)

    @stored
    @flushed
    def plus(user_id, entry_id):
        db.session.merge(Plus(user_id=user_id, entry_id=entry_id))
        if identity_key(Entry, entry_id) in db.session.identity_map:
            db.session.expire(Entry.query.get(entry_id), ['plus_count'])

    @stored
    @flushed
    def minus(user_id, entry_id):
        Plus.query.filter_by(user_id=user_id, entry_id=entry_id).delete()
        if identity_key(Entry, entry_id) in db.session.identity_map:
            db.session.expire(Entry.query.get(entry_id), ['plus_count'])

    @stored
    @flushed
    def plus_count(entry_id):
        return db.session.scalar(
            db.select([db.func.count('*')])
            .select_from(Plus.__table__)
            .where(Plus.entry_id == entry_id)
        )

    def _pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('PRAGMA cache_size = 100000')

    from sqlalchemy import event
    event.listen(db.engine, 'connect', _pragma_on_connect)

    db.create_all()
    db.configure_mappers()

    store.db = db
    return store
