import PIL.Image
from io import BytesIO


def kind(**kargs):
    if 'data' in kargs:
        input_stream = BytesIO(kargs['data'])
        pim = PIL.Image.open(input_stream)
        return pim.format.lower()
    else:
        assert False, 'invalid params'
