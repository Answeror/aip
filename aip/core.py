from .utils import thumbmd5
from . import tasks
from .log import Log
from . import work
from . import make as makeapp
from functools import partial
from flask import current_app
from .bed.baidupan import BaiduPan
from redis import Redis
from contextlib import contextmanager
from functools import wraps


log = Log(__name__)


def baidupan_redis_key(md5, width):
    return 'baidupan.' + thumbmd5(md5, width)


def sessioned(f):
    @wraps(f)
    def inner(self, *args, **kargs):
        if 'session' not in kargs:
            kargs['session'] = self.db.session
        return f(self, *args, **kargs)
    return inner


class Core(object):

    def __init__(
        self,
        db,
        baidupan_cookie=None,
        baidupan_timeout=30,
    ):
        self.db = db
        self.redis = Redis()
        if baidupan_cookie:
            self.baidupan = BaiduPan(baidupan_cookie)
        self.baidupan_timeout = baidupan_timeout

    def thumbnail_mtime_bi_md5(self, md5):
        return self.db.thumbnail_mtime_bi_md5(md5)

    def thumbnail_bi_md5(self, md5, width):
        return self.db.thumbnail_bi_md5(md5, width)

    def thumbnail_cache_timeout_bi_md5(self, md5):
        return self.db.thumbnail_cache_timeout_bi_md5(md5)

    def imgur_bi_md5(self, md5):
        return self.db.imgur_bi_md5(md5)

    def baidupan_thumbnail_linkout(self, md5, width):
        uri = self.redis.get(baidupan_redis_key(md5, width))
        if uri:
            uri = uri.decode('ascii')
            return uri

        if not hasattr(self, 'baidupan'):
            return None

        uri = self.baidupan.uri(thumbmd5(md5, width))
        if uri:
            self.redis.setex(
                baidupan_redis_key(md5, width),
                uri.encode('ascii'),
                self.baidupan_timeout,
            )
            return uri

        work.nonblock(
            tasks.persist_thumbnail_to_baidupan,
            makeapp=partial(makeapp, dbmode=True, **current_app.kargs),
            md5=md5,
            width=width,
        )

    def imgur_thumbnail_linkout(self, md5, width):
        bim = self.db.imgur_bi_md5(thumbmd5(md5, width))
        if bim:
            return bim.link.replace('http://', 'https://')
        work.nonblock(
            tasks.persist_thumbnail_to_imgur,
            makeapp=partial(makeapp, dbmode=True, **current_app.kargs),
            md5=md5,
            width=width,
        )

    def thumbnail_linkout(self, md5, width):
        for method in (
            self.baidupan_thumbnail_linkout,
            self.imgur_thumbnail_linkout,
        ):
            uri = method(md5, width)
            if uri:
                return uri

    def art_bi_md5(self, md5):
        return self.db.art_bi_md5(md5)

    @contextmanager
    def scoped_all_session(self):
        try:
            yield
        finally:
            from sqlalchemy.orm.session import Session
            Session.close_all()

    def user_bi_id(self, id):
        return self.db.get_user_bi_id(id)

    def user_bi_openid(self, openid):
        return self.db.get_user_bi_openid(openid)

    @sessioned
    def has_plused(self, user, art, session):
        '''http://stackoverflow.com/a/15314973/238472'''
        return session.scalar(
            self.db.select([
                self.db.exists('1')
                .select_from(self.db.table(self.db.Plus))
                .where(self.db.and_(
                    self.db.Plus.user_id == user.id,
                    self.db.Plus.entry_id == art.id,
                ))
            ])
        )
