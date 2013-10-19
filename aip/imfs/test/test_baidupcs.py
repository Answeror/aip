from nose.tools import assert_equal
from ..baidupcs import BaiduPCS
import os
import imghdr


CURRENT_PATH = os.path.dirname(__file__)

assert os.path.exists(os.path.join(CURRENT_PATH, 'access-token'))
with open(os.path.join(CURRENT_PATH, 'access-token'), 'rb') as f:
    access_token = f.read().decode('ascii').strip()

NERV = 'nerv_small.png'


class TestPCS(object):

    def setUp(self):
        self.pcs = BaiduPCS(access_token)
        self.pcs.remove(NERV)

    def test_save(self):
        name, data = load()
        assert not self.pcs.has(name)
        self.pcs.save(name, data)
        assert self.pcs.has(name)

    def test_load(self):
        name, data = load()
        self.pcs.save(name, data)
        assert_equal(self.pcs.load(name), data)

    def test_twice_save(self):
        name, data = load()
        self.pcs.save(name, data)
        self.pcs.save(name, data)

    def test_thumbnail(self):
        name, data = load()
        self.pcs.save(name, data)
        ret = self.pcs.thumbnail(name, 100, 100)
        assert_equal(imghdr.what('foo', ret), 'png')


def load():
    with open(os.path.join(CURRENT_PATH, NERV), 'rb') as f:
        return NERV, f.read()
