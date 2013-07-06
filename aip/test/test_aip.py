#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import assert_equal, assert_in, with_setup
from bs4 import BeautifulSoup as Soup
from flask import Flask
from .. import make
from .settings import RESPONSE_FILE_PATH
from mock import patch, Mock


g = type('g', (object,), {})()


def setup_app():
    g.app = Flask(__name__)
    g.aip = make()
    g.app.register_blueprint(g.aip)
    g.client = g.app.test_client()
    if hasattr(g, 'setup_store'):
        g.setup_store()


def teardown_app():
    if hasattr(g, 'teardown_store'):
        g.teardown_store()
    del g.client
    del g.app
    del g.aip


def patch_urllib3():
    def request(method, url):
        import pickle
        with open(RESPONSE_FILE_PATH, 'rb') as f:
            d = pickle.load(f)
        r = Mock()
        assert_equal(method, 'GET')
        assert_in(url, d)
        r.data = d[url]
        return r

    fake = Mock()
    fake.return_value.request = request
    g.patcher = patch('urllib3.PoolManager', fake)
    g.patcher.start()


def unpatch_urllib3():
    g.patcher.stop()


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_index_empty():
    r = g.client.get('/')
    soup = Soup(r.data)
    content = soup.find(id='items').get_text().strip()
    return assert_equal(content, '')


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_update_images():
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')
    g.client.get('/update_images/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'270')


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_no_duplication():
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')
    g.client.get('/update_images/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'270')
    g.client.get('/update_images/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'270')


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_clear():
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')
    g.client.get('/update_images/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'270')
    g.client.get('/clear')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')
