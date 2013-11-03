import PIL.Image
from io import BytesIO
from .log import Log
from .utils import calcmd5


log = Log(__name__)


def kind(**kargs):
    if 'data' in kargs:
        try:
            input_stream = BytesIO(kargs['data'])
            pim = PIL.Image.open(input_stream)
            return pim.format.lower()
        except:
            log.warning('unknown kind of {}', calcmd5(kargs['data']))
    else:
        assert False, 'invalid params'
