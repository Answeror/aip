import PIL.Image
from io import BytesIO


def thumbnail(data, kind, width, height):
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
