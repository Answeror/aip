#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import with_setup
from flask.ext.sqlalchemy import SQLAlchemy
from ..sqlalchemy import make
from ...test.test_aip import (
    g,
    setup_app,
    teardown_app,
    patch_urllib3,
    unpatch_urllib3,
    _test_index_empty,
    _test_update_images,
    _test_clear,
    _test_no_duplication
)
from ... import store_impl as memory


def setup_sqlalchemy():
    g.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    db = SQLAlchemy(g.app)
    g.aip.store = make(db)
    db.create_all()


def teardown_sqlalchemy():
    g.aip.store = memory


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def test_index_emtpy():
    _test_index_empty()


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def test_update_images():
    _test_update_images()


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def test_no_duplication():
    _test_no_duplication()


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def test_clear():
    _test_clear()
