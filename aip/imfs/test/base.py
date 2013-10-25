from nose.tools import assert_equal, assert_is, raises
import imghdr
from .const import NERV
from .utils import load_nerv
from ..base import NotFoundError


class Base(object):

    def __init__(self, make):
        self.make = make

    def setUp(self):
        self.fs = self.make()
        self.fs.remove(NERV)

    def tearDown(self):
        self.fs.remove(NERV)

    def test_save(self):
        name, data = load_nerv()
        assert not self.fs.has(name)
        self.fs.save(name, data)
        assert self.fs.has(name)

    def test_load(self):
        name, data = load_nerv()
        self.fs.save(name, data)
        assert_equal(self.fs.load(name), data)

    def test_twice_save(self):
        name, data = load_nerv()
        self.fs.save(name, data)
        self.fs.save(name, data)

    def test_thumbnail(self):
        name, data = load_nerv()
        self.fs.save(name, data)
        ret = self.fs.thumbnail(name, 100, 100)
        assert ret is not None
        assert_equal(imghdr.what('foo', ret), 'jpeg')

    def test_none(self):
        assert_is(self.fs.load(NERV), None)
        assert_is(self.fs.thumbnail(NERV, 100, 100), None)

    @raises(NotFoundError)
    def test_mtime_not_found(self):
        self.fs.mtime(NERV)

    def test_mtime(self):
        name, data = load_nerv()
        self.fs.save(name, data)
        self.fs.mtime(name)
