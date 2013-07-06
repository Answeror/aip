#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datetime import datetime
from sqlalchemy import func
from flask.ext.sqlalchemy import DeclarativeMeta
from collections import namedtuple
from .. import store


def _random_name():
    import uuid
    return str(uuid.uuid4())


def make(db):

    def noarg(t):
        return lambda primary_key=False, unique=False, **kargs: db.Column(
            t,
            primary_key=primary_key,
            unique=unique
        )

    FIELD_DICT = {
        str: lambda primary_key=False, unique=False, length=None, **kargs: db.Column(
            db.Text if length is None else db.String(length),
            primary_key=primary_key,
            unique=unique
        ),
        int: noarg(db.Integer),
        float: noarg(db.Float),
        bool: noarg(db.Boolean),
        datetime: noarg(db.DateTime),
        object: noarg(db.PickleType),
        bytes: noarg(db.LargeBinary)
    }

    class StoreMeta(store.StoreMeta):

        def __new__(meta, name, bases, attr):
            fields = []
            for base in bases:
                if hasattr(base, 'FIELDS'):
                    fields = getattr(base, 'FIELDS')
                    break

            for field in fields:
                if type(field) is tuple:
                    if len(field) == 2:
                        k, t = field
                        kargs = {}
                    elif len(field) == 3:
                        k, t, kargs = field
                    else:
                        assert False, 'wrong field format: {}'.format(field)
                else:
                    k = field
                    t = str
                    kargs = {}

                attr[k] = FIELD_DICT[t](**kargs)

            return store.StoreMeta.__new__(meta, name, bases, attr)

    class ModelMeta(StoreMeta, type(db.Model)):
        pass

    class Meta(store.Meta, db.Model, metaclass=ModelMeta):
        pass

    class Image(store.Image, db.Model, metaclass=ModelMeta):
        pass

    class Repo(store.Repo):

        def connection(self):
            return Connection()

        def clear(self):
            db.drop_all()
            db.create_all()

    class Connection(store.Connection):

        def __enter__(self, *args, **kargs):
            return self

        def __exit__(self, *args, **kargs):
            return

        def commit(self):
            db.session.commit()

        def add_or_update(self, o):
            if o.id is None:
                o.id = _random_name()
            o = db.session.merge(o)
            db.session.add(o)

        def put_image(self, im):
            if im.id is None:
                im.id = _random_name()

            origin = Image.query.filter_by(site_id=im.site_id, post_id=im.post_id).first()

            if origin is not None:
                im.id = origin.id
                im = db.session.merge(im)

            db.session.add(im)

        def put(self, o):
            return self.add_or_update(o)

        def get_images_order_bi_ctime(self, r):
            return Image.query.order_by(Image.ctime.desc())[r]

        def latest_ctime_bi_site_id(self, id):
            return db.session.query(func.max(Image.ctime)).first()[0]

        def image_count(self):
            return db.session.query(func.count(Image.id)).first()[0]

        def set_meta(self, id, value):
            self.put(Meta(id=id, value=value))

        def get_meta(self, id):
            return Meta.query.filter_by(id=id).first()

    Store = namedtuple('Store', ('Meta', 'Image', 'Repo', 'Connection'))
    return Store(
        Meta=Meta,
        Image=Image,
        Repo=Repo,
        Connection=Connection
    )
