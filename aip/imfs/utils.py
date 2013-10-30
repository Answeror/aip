import PIL.Image
from io import BytesIO
from ..log import Log
from nose.tools import assert_greater


log = Log(__name__)


#def thumbnail(data, kind, width, height):
    #try:
        #try:
            #from ..rq import q
            #from time import sleep
            #job = q.enqueue(use_wand, data, kind, width, height)
            #while job.result is None:
                #sleep(0.5)
            #ret = job.result
            #job.cancel()
            #return ret
        #except:
            #return use_wand(data, kind, width, height)
    #except:
        #return use_pil(data, kind, width, height)


def transparent(pim):
    '''http://stackoverflow.com/a/10689590/238472'''
    return pim.mode == "RGBA" or "transparency" in pim.info


def openpil(data):
    if type(data) is bytes:
        input_stream = BytesIO(data)
        return PIL.Image.open(input_stream)
    else:
        # pil image
        return data


def use_pil(data, kind, width, height, quality=80):
    pim = openpil(data)
    transp = transparent(pim)
    pim.thumbnail(
        (width, height),
        PIL.Image.ANTIALIAS
    )
    output_stream = BytesIO()
    if kind == 'gif' or pim.mode == 'P':
        pim = pim.convert('RGB')

    if transp:
        pim.save(output_stream, format='JPEG', quality=quality)
    else:
        pim.save(output_stream, format=kind.upper())

    return output_stream.getvalue()


def use_wand(data, kind, width, height):
    from wand.image import Image
    with Image(blob=data) as img:
        img.resize(width, height)
        return img.make_blob(kind)


def use_gifsicle(data, kind, width, height):
    import subprocess as sp
    import os
    from tempfile import NamedTemporaryFile as NTF

    with NTF(delete=False) as fin:
        fin.write(data)

    fout = NTF(delete=False)
    ferr = NTF(delete=False)
    try:
        ret = sp.call([
            'gifsicle',
            '--resize',
            '%dx%d' % (width, height),
            fin.name
        ], stderr=ferr, stdout=fout)
        if ret:
            raise Exception('gifsicle failed with %d' % ret)

        with open(fout.name, 'rb') as f:
            return f.read()
    finally:
        fout.close()
        os.unlink(fout.name)
        ferr.close()
        os.unlink(ferr.name)


def use_gifsicle_safe(*args, **kargs):
    try:
        return use_gifsicle(*args, **kargs)
    except:
        log.exception('thumbnail using gifsicle failed')


def use_pil_safe(*args, **kargs):
    try:
        return use_pil(*args, **kargs)
    except:
        log.exception('thumbnail using pil failed')


def thumbnail(data, kind, width, height):
    assert_greater(width, 0)
    assert_greater(height, 0)

    pim = openpil(data)
    if expanding(pim, width, height):
        return data
    if kind == 'gif':
        ret = use_gifsicle_safe(data, kind, width, height)
        if ret is not None:
            return ret
    return use_pil_safe(pim, kind, width, height)


def expanding(data, target_width, target_height):
    pim = openpil(data)
    source_width, source_height = pim.size
    eps = 1e-8
    return (
        source_width < target_width + eps and
        source_height < target_height + eps
    )
