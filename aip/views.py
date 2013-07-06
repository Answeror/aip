#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import g
from functools import wraps
import logging


def logged(f):
    @wraps(f)
    def inner(*args, **kargs):
        try:
            return f(*args, **kargs)
        except Exception as e:
            logging.exception(e)
            raise
    return inner


@logged
def update(begin):
    return g.aip.update(begin)


@logged
def posts(page):
    return g.aip.posts_in_page(page)


@logged
def stream(page):
    return g.aip.stream(page)


@logged
def resized(src, width, height):
    return g.aip.resized(src, width, height)


@logged
def image(src):
    return g.aip.image(src)


@logged
def image_count():
    return g.aip.image_count()


@logged
def update_images(begin):
    return g.aip.update_images(begin)


@logged
def last_update_time():
    return g.aip.last_update_time()


@logged
def style():
    return g.aip.scss()


@logged
def log():
    return g.aip.log()


@logged
def clear():
    return g.aip.clear()
