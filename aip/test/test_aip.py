#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import assert_equal, assert_in, with_setup
from bs4 import BeautifulSoup as Soup
from mock import patch, Mock
import os


RESPONSE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'response.pkl')
SQLALCHEMY_DATABASE_URI = 'sqlite://'


g = type('g', (object,), {})()


def setup_app():
    from .. import make
    g.app = make(__name__)



def teardown_app():
    del g.client
    del g.app


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


def _test_index_empty():
    r = g.client.get('/')
    soup = Soup(r.data)
    content = soup.find(id='items').get_text().strip()
    return assert_equal(content, '')


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_index_empty():
    _test_index_empty()


def _test_update_images():
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')
    g.client.get('/update/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'712')


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_update_images():
    _test_update_images()


def _test_unique_images():
    g.client.get('/update/20130630')
    r = g.client.get('/unique_image_count')
    assert_equal(r.data, b'504')
    r = g.client.get('/unique_image_md5')
    assert_equal(len(r.data.split(b'\n')), 504)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_unique_images():
    _test_unique_images()


def _test_no_duplication():
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')
    g.client.get('/update/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'712')
    g.client.get('/update/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'712')


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_no_duplication():
    _test_no_duplication()


def _test_clear():
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')
    g.client.get('/update/20130630')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'712')
    g.client.get('/clear')
    r = g.client.get('/image_count')
    assert_equal(r.data, b'0')


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_clear():
    _test_clear()
