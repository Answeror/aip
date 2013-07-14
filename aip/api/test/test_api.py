#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import (
    assert_true,
    assert_equal,
    assert_in,
    assert_not_in,
    with_setup
)
from mock import patch, Mock
import os
import json


RESPONSE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'response.pkl')
SQLALCHEMY_DATABASE_URI = 'sqlite://'


g = type('g', (object,), {})()


def api(path):
    return g.app.config['AIP_API_URL_PREFIX'] + path


def setup_app():
    from ... import make as make_app
    from .. import make as make_api
    g.app = make_app(__name__)
    make_api(g.app)
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
        assert_in(url, d)
        r.data = d[url]
        return r

    fake = Mock()
    fake.return_value.request = request
    g.patcher = patch('urllib3.PoolManager', fake)
    g.patcher.start()


def unpatch_urllib3():
    g.patcher.stop()


def add_user():
    r = g.client.get(api('/user_count'))
    assert_equal(result(r), 0)
    r = g.client.post(api('/add_user'), content_type='application/json', data=json.dumps(dict(
        openid='openid',
        name='Cosmo Du',
        email='answeror@gmail.com'
    )))
    assert_success(r)
    r = g.client.get(api('/user_count'))
    assert_equal(result(r), 1)


def update():
    r = g.client.get(api('/update/20130630'))
    assert_success(r)


def assert_success(r):
    assert_not_in('error', json.loads(r.data.decode('utf-8')))


def result(r):
    return json.loads(r.data.decode('utf-8'))['result']


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_add_user():
    r = g.client.get(api('/user_count'))
    assert_equal(result(r), 0)
    r = g.client.post(api('/add_user'), content_type='application/json', data=json.dumps(dict(
        openid='openid',
        name='Cosmo Du',
        email='answeror@gmail.com'
    )))
    assert_success(r)
    r = g.client.get(api('/user_count'))
    assert_equal(result(r), 1)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_update_images():
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 0)
    r = g.client.get(api('/update/20130630'))
    assert_success(r)
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 712)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_entries():
    r = g.client.get(api('/update/20130630'))
    assert_success(r)
    r = g.client.get(api('/entry_count'))
    assert_equal(result(r), 504)
    r = g.client.get(api('/entries'))
    assert_equal(len(result(r)), 504)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_no_duplication():
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 0)
    r = g.client.get(api('/update/20130630'))
    assert_success(r)
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 712)
    r = g.client.get(api('/update/20130630'))
    assert_success(r)
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 712)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_clear():
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 0)
    r = g.client.get(api('/update/20130630'))
    assert_success(r)
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 712)
    r = g.client.get(api('/clear'))
    assert_success(r)
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 0)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
@with_setup(add_user)
@with_setup(update)
def test_plus():
    r = g.client.get(
        api('/plused'),
        content_type='application/json',
        data=json.dumps(dict(user_openid='openid'))
    )
    assert_equal(len(result(r)), 0)
    r = g.client.get(api('/entries'))
    assert_success(r)
    entry_id = result(r)[0]['id']
    r = g.client.post(
        api('/plus'),
        content_type='application/json',
        data=json.dumps(dict(
            user_openid='openid',
            entry_id=entry_id
        ))
    )
    assert_success(r)
    r = g.client.get(
        api('/plused'),
        content_type='application/json',
        data=json.dumps(dict(user_openid='openid'))
    )
    assert_equal(len(result(r)), 1)
    r = g.client.post(
        api('/minus'),
        content_type='application/json',
        data=json.dumps(dict(
            user_openid='openid',
            entry_id=entry_id
        ))
    )
    assert_success(r)
    r = g.client.get(
        api('/plused'),
        content_type='application/json',
        data=json.dumps(dict(user_openid='openid'))
    )
    assert_equal(len(result(r)), 0)
