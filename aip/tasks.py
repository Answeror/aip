from .utils import md5 as calcmd5
from .log import Log


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
