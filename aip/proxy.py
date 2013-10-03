from flask import current_app
from .bed.immio import Immio
from .bed.imgur import Imgur
import logging


def ex():
    return current_app.config['AIP_EXECUTOR']


def immio_url(store, md5):
    im = store.Entry.get_bi_md5(md5)
    immio_image = store.get_immio_bi_md5(md5)
    immio = Immio(
        max_size=current_app.config['AIP_IMMIO_RESIZE_MAX_SIZE'],
        timeout=current_app.config['AIP_UPLOAD_IMMIO_TIMEOUT']
    )
    if immio_image:
        logging.info('hit %s' % md5)
    else:
        immio_image = ex().submit(
            immio.upload,
            url=im.sample_url if im.sample_url else im.image_url,
            md5=im.md5
        ).result()
        immio_image = store.Immio(
            uid=immio_image.uid,
            md5=immio_image.md5,
            uri=immio_image.uri,
            width=immio_image.width,
            height=immio_image.height
        )
        store.db.session.flush()
        immio_image = store.db.session.merge(immio_image)
        store.db.session.commit()
    return immio_image.uri


def imgur_url(store, md5, width=None, resolution=None):
    im = store.Entry.get_bi_md5(md5)
    imgur_image = store.get_imgur_bi_md5(md5)
    limit = current_app.config['AIP_IMGUR_RESIZE_LIMIT']
    if resolution is None:
        resolution = current_app.config['AIP_RESOLUTION_LEVEL']
    imgur = Imgur(
        client_ids=current_app.config['AIP_IMGUR_CLIENT_IDS'],
        resolution_level=resolution,
        max_size=(limit, limit),
        timeout=current_app.config['AIP_UPLOAD_IMGUR_TIMEOUT'],
        album_deletehash=current_app.config['AIP_IMGUR_ALBUM_DELETEHASH']
    )
    if imgur_image:
        logging.info('hit %s' % md5)
    else:
        imgur_image = ex().submit(
            imgur.upload,
            url=im.sample_url if im.sample_url else im.image_url,
            md5=im.md5
        ).result()
        imgur_image = store.Imgur(
            id=imgur_image.id,
            md5=imgur_image.md5,
            link=imgur_image.link,
            deletehash=imgur_image.deletehash
        )
        store.db.session.flush()
        imgur_image = store.db.session.merge(imgur_image)
        store.db.session.commit()
    if width is not None:
        height = width * im.height / im.width
        url = imgur.best_link(imgur_image, width, height)
    else:
        url = imgur_image.link

    return url.replace('http://', 'https://')
