#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import assert_equal, with_setup
from bs4 import BeautifulSoup as Soup
from mock import patch, Mock
import os


RESPONSE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'response.pkl')
SQLALCHEMY_DATABASE_URI = 'sqlite://'


g = type('g', (object,), {})()


def setup_app():
    from .. import make
    g.app = make(__name__)
    g.client = g.app.test_client()


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
        if url not in d:
            raise Exception('url %s not in cache' % url)
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


