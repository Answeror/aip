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


def use_pil(data, kind, width, height):
    import PIL.Image
    from io import BytesIO
    input_stream = BytesIO(data)
    pim = PIL.Image.open(input_stream)
    pim.thumbnail(
        (width, height),
        PIL.Image.ANTIALIAS
    )
    output_stream = BytesIO()
    if kind == 'gif':
        pim = pim.convert('RGB')
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

        print('use gifsicle')

        with open(fout.name, 'rb') as f:
            return f.read()
    finally:
        fout.close()
        os.unlink(fout.name)
        ferr.close()
        os.unlink(ferr.name)


def thumbnail(data, kind, width, height):
    if kind == 'gif':
        try:
            return use_gifsicle(data, kind, width, height)
        except:
            pass
    return use_pil(data, kind, width, height)
