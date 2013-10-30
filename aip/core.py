from .utils import thumbmd5
from . import tasks
from .log import Log
from . import work
from . import make as makeapp
from functools import partial
from flask import current_app
from .bed.baidupan import BaiduPan


log = Log(__name__)


class Core(object):

    def __init__(
        self,
        db,
        baidupan_cookie=None,
    ):
        self.db = db
        if baidupan_cookie:
            self.baidupan = BaiduPan(baidupan_cookie)

    def thumbnail_mtime_bi_md5(self, md5):
        return self.db.thumbnail_mtime_bi_md5(md5)

    def thumbnail_bi_md5(self, md5, width):
        return self.db.thumbnail_bi_md5(md5, width)

    def thumbnail_cache_timeout_bi_md5(self, md5):
        return self.db.thumbnail_cache_timeout_bi_md5(md5)

    def imgur_bi_md5(self, md5):
        return self.db.imgur_bi_md5(md5)

    def baidupan_thumbnail_linkout(self, md5, width):
        if not hasattr(self, 'baidupan'):
            return None
        uri = self.baidupan.uri(thumbmd5(md5, width))
        if uri:
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
            return bim.link.replace('http://', '//')
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
