#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, desc
from sqlalchemy.ext.hybrid import hybrid_property
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
        posts = db.relationship('Post')

        @hybrid_property
        def ctime(self):
            if not hasattr(self, '_ctime'):
                self._ctime = db.session.query(func.min(Post.ctime)).filter(Post.md5 == self.id)
            return self._ctime

        @ctime.expression
        def ctime(cls):
            return db.session.query(func.min(Post.ctime)).filter(Post.md5 == cls.id)

        @hybrid_property
        def best_post(self):
            if not hasattr(self, '_best_post'):
                #self._best_post = Post.query.filter_by(md5=self.id).first()
                #sub = Post.query.filter_by(md5=self.id).subquery()
                #self._best_post = db.session.query(sub).filter(sub.c.score == func.max(sub.c.score).select()).first()
                sub = db.session.query(
                    Post.md5,
                    func.max(Post.score).label('score'),
                ).group_by(Post.md5).subquery()
                self._best_post = Post.query.outerjoin(sub, Post.md5 == sub.c.md5).filter_by(md5=self.id).first()
            return self._best_post

        @property
        def plus_count(self):
            if not hasattr(self, '_plus_count'):
                self._plus_count = db.session.query(User).with_parent(self, 'plused').count()
            return self._plus_count

        @property
        def post_url(self):
            return self.best_post.post_url

        @property
        def preview_url(self):
            return self.best_post.preview_url

        @property
        def preview_width(self):
            return self.ideal_width

        @property
        def preview_height(self):
            return int(self.ideal_width * self.best_post.height / self.best_post.width)

        @property
        def md5(self):
            return self.id

        @property
        def score(self):
            return self.best_post.score

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
