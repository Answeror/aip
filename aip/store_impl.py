#!/usr/bin/env python
# -*- coding: utf-8 -*-


from operator import attrgetter as attr
import abc
from functools import partial
from . import store


def _data(field):
    return '_%s' % field


class StoreMeta(store.StoreMeta):

    def __new__(meta, name, bases, attr):
        for base in bases:
            if hasattr(base, 'FIELDS'):
                fields = getattr(base, 'FIELDS')
                break
        for field in fields:
            if type(field) is tuple:
                key = field[0]
            else:
                key = field

            # cannot use lambda here!
            def get(key, self):
                return getattr(self, _data(key)) if hasattr(self, _data(key)) else None

            def set(key, self, value):
                setattr(self, _data(key), value)

            attr[key] = property(
                partial(get, key),
                partial(set, key)
            )
        return store.StoreMeta.__new__(meta, name, bases, attr)

    def __call__(cls, **kargs):
        inst = store.StoreMeta.__call__(cls)
        for key, value in list(kargs.items()):
            setattr(inst, _data(key), value)
        return inst


class Meta(store.Meta, metaclass=StoreMeta):
    pass


class User(store.User, metaclass=StoreMeta):
    pass


class Image(store.Image, metaclass=StoreMeta):
    pass


class Repo(store.Repo):

    def __init__(self):
        self.images = []
        self.meta = {}
        self.users = []

    def connection(self):
        return Connection(self)

    def clear(self):
        self.images = []
        self.meta = {}


def _random_name():
    import uuid
    return uuid.uuid4()


def unique(a, key):
    '''http://www.peterbe.com/plog/uniqifiers-benchmark'''
    seen = {}
    result = []
    for e in a:
        if not key(e) in seen:
            seen[key(e)] = 1
            result.append(e)
    return result


class Connection(store.Connection):

    @property
    def images(self):
        return self.repo.images

    @property
    def meta(self):
        return self.repo.meta

    @property
    def users(self):
        return self.repo.users

    def __init__(self, repo):
        self.repo = repo

    def __enter__(self, *args, **kargs):
        return self

    def __exit__(self, *args, **kargs):
        pass

    def commit(self):
        pass

    def put_image(self, im):
        if im.id is None:
            im.id = _random_name()

        origin = None
        for other in self.images:
            if other.id == im.id:
                origin = other
            elif other.site_id == im.site_id and other.post_id == im.post_id:
                origin = other
            if origin is not None:
                break

        if not origin:
            self.images.append(im)
        else:
            im.id = origin.id
            for key, value in list(im.__dict__.items()):
                if value is not None:
                    setattr(origin, key, value)

    def put(self, o):
        return self.add_or_update(o)

    def add_or_update(self, o):
        if type(o) is Image:
            self.put_image(o)
        else:
            raise Exception('unknown model: {0}'.format(type(o)))

    def get_images_order_bi_ctime(self, r=None):
        ims = sorted(self.images, key=attr('ctime'), reverse=True)
        return ims if r is None else ims[r]

    def get_unique_images_order_bi_ctime(self, r=None):
        return unique(self.get_images_order_bi_ctime(r), key=lambda im: im.md5)

    def latest_ctime_bi_site_id(self, id):
        images = [im for im in self.images if im.site_id == id]
        if not images:
            return None
        return max([im.ctime for im in images])

    def image_count(self):
        return len(self.images)

    def user_count(self):
        return len(self.users)

    def unique_image_count(self):
        return len(unique(self.images, key=lambda im: im.md5))

    def set_meta(self, id, value):
        self.meta[id] = value

    def get_meta(self, id):
        return self.meta.get(id, None)

    def get_image_bi_md5(self, md5):
        for im in self.images:
            if im.md5 == md5:
                return im
        return None

    def get_user_bi_id(self, id):
        for user in self.users:
            if im.id == id:
                return user
        return None
