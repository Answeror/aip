#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import with_setup
from flask.ext.sqlalchemy import SQLAlchemy
from ..sqlalchemy import make
from ...test.test_aip import (
    g,
    test_config,
    test_index_empty,
    test_update_sites,
    test_update_images
)
from ... import store_impl as memory


def setup_sqlalchemy():
    def setup_store():
        g.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db = SQLAlchemy(g.app)
        g.aip.store = make(db)
        db.create_all()

    def teardown_store():
        g.aip.store = memory

    g.setup_store = setup_store
    g.teardown_store = teardown_store


def teardown_sqlalchemy():
    del g.setup_store
    del g.teardown_store


@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def _test_config():
    test_config()


@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def _test_index_emtpy():
    test_index_empty()


@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def _test_update_sites():
    test_update_sites()


@with_setup(setup_sqlalchemy, teardown_sqlalchemy)
def _test_update_images():
    test_update_images()
