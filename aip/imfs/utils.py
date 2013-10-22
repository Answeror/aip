import PIL.Image
from io import BytesIO


def thumbnail(data, kind, width, height):
    try:
        return use_wand(data, kind, width, height)
    except:
        return use_pil(data, kind, width, height)


def use_pil(data, kind, width, height):
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
