#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def make_children(parents):
    children = {}
    for c, ps in parents.items():
        children[c] = children.get(c, set())
        for p in ps:
            children[p] = children.get(p, set())
            children[p].add(c)
    return children


def make_parent_count(parents):
    return {c: len(ps) for c, ps in parents.items()}


def toporder(parents):
    children = make_children(parents)
    parent_count = make_parent_count(parents)
    q = []
    for i, c in parent_count.items():
        if c == 0:
            q.append(i)
    while q:
        root = q.pop()
        yield root
        for child in children[root]:
            parent_count[child] -= 1
            if parent_count[child] == 0:
                q.append(child)


def buildup(parents):
    up = {}
    for i in toporder(parents):
        up[i] = set()
        up[i].update(parents[i])
        for p in parents[i]:
            up[i].update(up[p])
    return up


class Base(object):

    def __init__(self):
        self.parents = {}
        self.up = {}

    def add(self, id):
        self.parents[id] = self.parents.get(id, set())
        self.up[id] = self.up.get(id, set())

    def link(self, child, parent):
        self.parents[child].add(parent)
        s = self.up[child]
        s.update(self.parents[parent])
        s.add(parent)

    def propagate(self, id, down):
        for i in down[id]:
            self.up[i].update(self.up[id])

    def remove(self, id):
        del self.parents[id]
        for _, ps in self.parents.items():
            ps.discard(id)
        self.up = buildup(self.parents)

    def unlink(self, child, parent):
        self.parents[child].discard(parent)
        self.up = buildup(self.parents)

    def to_dict(self):
        return {
            'parents': self.parents,
            'up': self.up
        }

    @classmethod
    def from_dict(cls, d):
        inst = cls()
        inst.parents = d['parents']
        inst.up = d['up']
        return inst


class Dag(object):

    def __init__(self):
        self.forward = Base()
        self.backward = Base()

    def add(self, id):
        self.forward.add(id)
        self.backward.add(id)

    def link(self, child, parent):
        self.forward.link(child, parent)
        self.backward.link(parent, child)
        self.forward.propagate(child, self.down)
        self.backward.propagate(parent, self.up)

    def remove(self, id):
        self.forward.remove(id)
        self.backward.remove(id)

    def unlink(self, child, parent):
        self.forward.unlink(child, parent)
        self.backward.unlink(parent, child)

    @property
    def parents(self):
        return self.forward.parents

    @property
    def children(self):
        return self.backward.parents

    @property
    def up(self):
        return self.forward.up

    @property
    def down(self):
        return self.backward.up

    def to_dict(self):
        return {
            'forward': self.forward.to_dict(),
            'backward': self.backward.to_dict()
        }

    @classmethod
    def from_dict(cls, d):
        inst = cls()
        inst.forward = Base.from_dict(d['forward'])
        inst.backward = Base.from_dict(d['backward'])
        return inst
