#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Infinite(object):

    def __init__(self, page, per, fetch):
        self.page = page
        self.per = per
        self.fetch = fetch

    @property
    def items(self):
        if not hasattr(self, '_items'):
            self._items = list(self.fetch(self.page, self.per))
        return self._items

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return len(self.items) >= self.per

    @property
    def prev(self):
        return self.page - 1 if self.has_prev else None

    @property
    def next(self):
        return self.page + 1 if self.has_next else None
