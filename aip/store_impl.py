#!/usr/bin/env python
# -*- coding: utf-8 -*-


from operator import attrgetter as attr
from . import store


class Image(store.Image):

    def __init__(self, **kargs):
        for key, value in list(kargs.items()):
            setattr(self, key, value)


class Site(store.Site):

    def __init__(self, **kargs):
        for key, value in list(kargs.items()):
            setattr(self, key, value)


class Cache(store.Cache):

    def __init__(self, id, data, meta):
        self.id = id
        self.data = data
        self.meta = meta


class Repo(store.Repo):

    def __init__(self):
        self.images = []
        self.sites = []
        self.cache = []

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
    def cache(self):
        return self.repo.cache

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
        elif type(o) is Cache:
            self._add_or_update(o, self.cache)
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

    def get_cache_bi_id(self, id):
        for c in self.cache:
            if c.id == id:
                return c
        return None

    def site_count(self):
        return len(self.sites)

    def image_count(self):
        return len(self.images)
