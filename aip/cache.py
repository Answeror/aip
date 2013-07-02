#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Pool(object):

    def __init__(self, aip, max_size=65536, max_items=1024):
        self.aip = aip
        self.max_size = max_size
        self.max_items = max_items

    def coned(f):
        def inner(self, *args, **kargs):
            with self._connection() as con:
                ret = f(self, con, *args, **kargs)
                con.commit()
                return ret
        return inner

    @coned
    def has(self, con, id):
        return con.get_cache_bi_id(id) is not None

    @coned
    def get(self, con, id):
        return con.get_cache_bi_id(id)

    @coned
    def put(self, con, cache):
        con.add_or_update(cache)
        while con.cache_count() >= self.max_items or con.cache_size() >= self.max_size:
            con.delete_one_cache()
