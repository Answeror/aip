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
        except (KeyboardInterrupt, SystemExit):
            raise
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
def sample(md5):
    return g.aip.sample(md5)


@logged
def image_count():
    return g.aip.image_count()


@logged
def unique_image_count():
    return g.aip.unique_image_count()


@logged
def unique_image_md5():
    return g.aip.unique_image_md5()


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


@logged
def login():
    return g.aip.login()


@logged
def create_or_login(resp):
    return g.aip.create_or_login(resp)


@logged
def create_profile():
    return g.aip.create_profile()


@logged
def logout():
    return g.aip.logout()


@logged
def user_count():
    return g.aip.user_count()
