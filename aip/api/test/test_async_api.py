#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from nose.tools import (
    assert_equal,
    assert_in,
    assert_not_in,
    with_setup
)
from mock import patch, Mock
import os
import json
import urllib3
import time
import tempfile


RESPONSE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'response.pkl')
dbf = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
dbf.close()
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % dbf.name
with open(os.path.join(os.path.dirname(__file__), 'imgur.json'), 'rb') as f:
    imgur_conf = json.loads(f.read().decode('ascii'))
    AIP_IMGUR_CLIENT_IDS = imgur_conf['client_ids']
    AIP_IMGUR_ALBUM_ID = imgur_conf['album']['id']
    AIP_IMGUR_ALBUM_DELETEHASH = imgur_conf['album']['deletehash']


g = type('g', (object,), {})()


def api(path):
    return g.app.config['AIP_API_URL_PREFIX'] + path


def setup_app():
    from ... import make
    g.app = make(__name__)
    g.client = g.app.test_client()


def teardown_app():
    del g.client
    del g.app


def patch_urllib3():
    real = urllib3.PoolManager()

    def request(*args, **kargs):
        if len(args) > 1:
            url = args[1]
        else:
            url = kargs['url']

        if url.startswith('https://api.imgur.com'):
            return real.request(*args, **kargs)

        import pickle
        with open(RESPONSE_FILE_PATH, 'rb') as f:
            d = pickle.load(f)
        r = Mock()
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
    r = json.loads(r.data.decode('utf-8'))
    assert_in('result', r)
    return r['result']


def pump(ids):
    for i in range(10):
        time.sleep(1)
        r = g.client.post(
            api('/async/pump'),
            content_type='application/json',
            data=json.dumps(dict(ids=ids, interval=20))
        )
        assert_success(r)
        if result(r):
            break
    else:
        assert False, 'pump failed'


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_async_update_images():
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 0)
    r = g.client.get(api('/async/update/20130630'))
    assert_success(r)
    assert_in('id', result(r))
    id = result(r)['id']
    pump([id])
    r = g.client.get(api('/image_count'))
    assert_equal(result(r), 712)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
@with_setup(add_user)
@with_setup(update)
def test_async_plus():
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
        api('/async/plus'),
        content_type='application/json',
        data=json.dumps(dict(
            user_openid='openid',
            entry_id=entry_id
        ))
    )
    assert_success(r)
    assert_in('id', result(r))
    id = result(r)['id']
    pump([id])
    r = g.client.get(
        api('/plused'),
        content_type='application/json',
        data=json.dumps(dict(user_openid='openid'))
    )
    assert_equal(len(result(r)), 1)
    r = g.client.post(
        api('/async/minus'),
        content_type='application/json',
        data=json.dumps(dict(
            user_openid='openid',
            entry_id=entry_id
        ))
    )
    assert_success(r)
    assert_in('id', result(r))
    id = result(r)['id']
    pump([id])
    r = g.client.get(
        api('/plused'),
        content_type='application/json',
        data=json.dumps(dict(user_openid='openid'))
    )
    r = g.client.get(
        api('/plused'),
        content_type='application/json',
        data=json.dumps(dict(user_openid='openid'))
    )
    assert_equal(len(result(r)), 0)


@with_setup(patch_urllib3, unpatch_urllib3)
@with_setup(setup_app, teardown_app)
def test_async_proxied_url():
    r = g.client.get(api('/update/20130630'))
    assert_success(r)
    r = result(g.client.get(api('/entries')))
    r = g.client.get(api('/async/proxied_url/%s' % r[0]['id']))
    assert_success(r)
    assert_in('id', result(r))
    id = result(r)['id']
    pump([id])
