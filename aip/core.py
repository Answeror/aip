from .utils import thumbmd5
from . import tasks
from .log import Log
from . import work
from flask import (
    current_app,
    copy_current_request_context,
)
from .bed.baidupan import BaiduPan
from redis import Redis
from contextlib import contextmanager
from functools import wraps


log = Log(__name__)


class CoreError(Exception):
    pass


def baidupan_redis_key(md5, width):
    return ':'.join(['baidupan', thumbmd5(md5, width)])


def sessioned(f):
    @wraps(f)
    def g(self, *args, **kargs):
        if 'session' not in kargs:
            with self.make_session() as session:
                kargs['session'] = session
                kargs['commit'] = True
                return f(self, *args, **kargs)
        else:
            if 'commit' not in kargs:
                kargs['commit'] = False
            return f(self, *args, **kargs)
    return g


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

    @contextmanager
    def make_session(self):
        s = self.db.create_scoped_session()
        try:
            yield s
        finally:
            s.remove()

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

        detail = self.baidupan.uri_detail(
            thumbmd5(md5, width),
            life=self.baidupan_timeout,
        )
        if detail:
            life = int(max(self.baidupan_timeout, detail.life - 60))
            log.debug('{} life: {}', detail.uri, life)
            self.redis.setex(
                baidupan_redis_key(md5, width),
                detail.uri.encode('ascii'),
                life,
            )
            return detail.uri

        work.nonblock_call(
            copy_current_request_context(tasks.persist_thumbnail_to_baidupan),
            kargs=dict(
                makeapp=lambda: current_app,
                md5=md5,
                width=width,
            ),
            bound='io',
        )

    def imgur_thumbnail_linkout(self, md5, width):
        bim = self.db.imgur_bi_md5(thumbmd5(md5, width))
        if bim:
            return bim.link.replace('http://', 'https://')
        work.nonblock_call(
            copy_current_request_context(tasks.persist_thumbnail_to_imgur),
            kargs=dict(
                makeapp=lambda: current_app,
                md5=md5,
                width=width,
            ),
            bound='io',
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

    @sessioned
    def art_detail_bi_md5(self, md5, session, commit):
        art = (
            session.query(self.db.Entry)
            .filter_by(md5=md5)
            .options(self.db.joinedload(self.db.Entry.posts, inner=True))
            .options(self.db.subqueryload(self.db.Entry.tags))
            .first()
        )
        if art:
            # touch it, to prevent session expire
            art.plus_count
        return art

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
    def has_plused(self, user, art, session, commit):
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

    @sessioned
    def plus_count(self, art_id, session, commit):
        return session.scalar(
            self.db.select([self.db.func.count('*')])
            .select_from(self.db.table(self.db.Plus))
            .where(self.db.Plus.entry_id == art_id)
        )

    @sessioned
    def plus(self, user_id, art_id, session, commit):
        session.execute(
            self.db.table(self.db.Plus).insert(dict(
                user_id=user_id,
                entry_id=art_id,
            ))
        )
        if commit:
            from sqlalchemy.exc import IntegrityError
            try:
                session.commit()
            except IntegrityError as e:
                code, _ = e.orig
                # http://stackoverflow.com/q/8072537/238472
                if code == 1062:
                    log.warning('duplicated plus ({}, {})', user_id, art_id)
                    pass
                else:
                    session.rollback()

    @sessioned
    def minus(self, user_id, art_id, session, commit):
        session.execute(
            self.db.table(self.db.Plus).delete(
                self.db.and_(
                    self.db.Plus.user_id == user_id,
                    self.db.Plus.entry_id == art_id,
                )
            )
        )
        if commit:
            try:
                session.commit()
            except:
                session.rollback()
                log.exception('minus ({}, {}) failed', user_id, art_id)
                raise CoreError(
                    'minus ({}, {}) failed due to database error',
                    user_id,
                    art_id
                )

    @sessioned
    def set_baidupcs_access_token(self, value, session, commit):
        session.merge(self.db.Meta(
            id='baidupcs_access_token',
            value=value.encode('ascii')
        ))
        if commit:
            session.commit()

    @sessioned
    def set_baidupcs_refresh_token(self, value, session, commit):
        session.merge(self.db.Meta(
            id='baidupcs_refresh_token',
            value=value.encode('ascii')
        ))
        if commit:
            session.commit()

    @sessioned
    def baidupcs_access_token(self, session, commit):
        return session.query(self.db.Meta).get('baidupcs_access_token')
