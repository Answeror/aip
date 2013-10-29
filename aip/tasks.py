from .utils import md5 as calcmd5
from .log import Log
from datetime import datetime, timedelta
from time import time
from flask import (
    current_app,
)
import os
from fn.iters import chain
from functools import partial
import pickle


log = Log(__name__)


def persist_thumbnail(makeapp, md5, width):
    app = makeapp()

    from .bed.imgur import Imgur
    bed = Imgur(
        client_ids=app.config['AIP_IMGUR_CLIENT_IDS'],
        timeout=app.config['AIP_UPLOAD_IMGUR_TIMEOUT'],
        album_deletehash=app.config['AIP_IMGUR_ALBUM_DELETEHASH']
    )

    thumbmd5 = calcmd5(('%s.%d' % (md5, width)).encode('ascii'))

    with app.test_request_context():
        data = app.store.thumbnail_bi_md5(md5, width)
        r = bed.upload(
            data=data,
            md5=thumbmd5,
        )
        if r is None:
            log.info('imgur upload failed: ({}, {})', md5, width)
        else:
            app.store.session.flush()
            app.store.session.merge(app.store.Imgur(
                id=r.id,
                md5=r.md5,
                link=r.link,
                deletehash=r.deletehash
            ))
            app.store.session.commit()


def test_log():
    log.info('work')


def update(begin, makeapp):
    app = makeapp()
    with app.test_request_context():
        now = datetime.utcnow()
        _update_images(begin)
        _set_last_update_time(now)
        current_app.store.db.session.commit()


def update_past(seconds, makeapp):
    app = makeapp()
    with app.test_request_context():
        now = datetime.utcnow()
        _update_images(now - timedelta(seconds=seconds))
        _set_last_update_time(now)
        current_app.store.db.session.commit()


def makesources():
    def gen():
        import pkgutil
        import importlib
        from inspect import isabstract
        from . import sources
        sources_folder = os.path.dirname(sources.__file__)
        for _, name, _ in list(pkgutil.iter_modules([sources_folder])):
            module = importlib.import_module('.sources.' + name, 'aip')
            if hasattr(module, 'Source'):
                source = getattr(module, 'Source')
                if not isabstract(source):
                    yield source
    return list(gen())


def _update_images(begin=None, limit=65536):
    start = time()
    sources = [make(dict) for make in makesources()]

    from concurrent.futures import ThreadPoolExecutor as Ex
    with Ex(len(sources)) as ex:
        posts = list(chain.from_iterable(
            ex.map(partial(fetch_posts, begin, limit), sources)
        ))

    log.info(
        'fetch posts done, {} fetched, take {}',
        len(posts),
        time() - start
    )
    start = time()
    current_app.store.Post.puts(posts=posts)
    log.info('put posts done, take {}', time() - start)


def _set_last_update_time(value):
    current_app.store.set_meta('last_update_time', pickle.dumps(value))


def fetch_posts(begin, limit, source):
    def gen():
        tags = []
        for _, post in zip(list(range(limit)), source.get_images(tags)):
            if begin is not None and post['ctime'] <= begin:
                break
            yield post
    return list(gen())
