from .utils import md5 as calcmd5
from . import tasks
from .log import Log
from . import work
from . import make as makeapp
from functools import partial
from flask import current_app


log = Log(__name__)


def Core(object):

    def __init__(self, db):
        self.db = db

    def thumbnail_mtime_bi_md5(self, md5):
        return self.db.thumbnail_mtime_bi_md5(md5)

    def thumbnail_bi_md5(self, md5, width):
        return self.db.thumbnail_bi_md5(md5, width)

    def thumbnail_cache_timeout_bi_md5(self, md5):
        return self.db.thumbnail_cache_timeout_bi_md5(md5)

    def imgur_bi_md5(self, md5):
        return self.db.imgur_bi_md5(md5)

    def thumbnail_linkout(self, md5, width):
        thumbmd5 = calcmd5(('%s.%d' % (md5, width)).encode('ascii'))
        bim = self.db.imgur_bi_md5(thumbmd5)
        if bim:
            #log.info('imgur hit %s, width %d' % (md5, width))
            return bim.link.replace('http://', 'https://')

        work.nonblock(
            tasks.persist_thumbnail,
            makeapp=partial(makeapp, dbmode=True, **current_app.kargs),
            md5=md5,
            width=width,
        )

    def art_bi_md5(self, md5):
        return self.db.art_bi_md5(md5)
