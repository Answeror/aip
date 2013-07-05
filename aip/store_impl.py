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


class Image(store.Image, metaclass=StoreMeta):
    pass


class Site(store.Site, metaclass=StoreMeta):
    pass


class Repo(store.Repo):

    def __init__(self):
        self.images = []
        self.sites = []
        self.meta = {}

    def connection(self):
        return Connection(self)


def _random_name():
    import uuid
    return uuid.uuid4()


class Connection(store.Connection):

    @property
    def images(self):
        return self.repo.images

    @property
    def sites(self):
        return self.repo.sites

    @property
    def meta(self):
        return self.repo.meta

    def __init__(self, repo):
        self.repo = repo

    def __enter__(self, *args, **kargs):
        return self

    def __exit__(self, *args, **kargs):
        pass

    def commit(self):
        pass

    def _add_or_update(self, o, os):
        if o.id is None:
            o.id = _random_name()
            os.append(o)
        else:
            append = True
            for other in os:
                if other.id == o.id:
                    for key, value in list(o.__dict__.items()):
                        if value is not None:
                            setattr(other, key, value)
                    append = False
                    break
            if append:
                os.append(o)

    def add_or_update(self, o):
        if type(o) is Image:
            self._add_or_update(o, self.images)
        elif type(o) is Site:
            self._add_or_update(o, self.sites)
        else:
            raise Exception('unknown model: {0}'.format(type(o)))

    def get_images_order_bi_ctime(self, r):
        for i, im in enumerate(sorted(self.images, key=attr('ctime'), reverse=True)):
            if i in r:
                yield im

    def get_site_bi_id(self, id):
        for s in self.sites:
            if s.id == id:
                return s
        return None

    def latest_ctime_bi_site_id(self, id):
        images = [im for im in self.images if im.site_id == id]
        if not images:
            return None
        return max([im.ctime for im in images])

    def site_count(self):
        return len(self.sites)

    def image_count(self):
        return len(self.images)

    def set_meta(self, id, value):
        self.meta[id] = value

    def get_meta(self, id):
        return self.meta.get(id, None)
