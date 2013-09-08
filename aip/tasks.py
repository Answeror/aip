from celery.utils.log import get_task_logger
from .bunch import Bunch


log = get_task_logger(__name__)


def make(celery):

    @celery.task()
    def upload(bed, *args, **kargs):
        print('foooooooooooooooooooooooooooooooo')
        log.info('%s upload start' % bed.name)
        return bed.upload(*args, **kargs)

    return Bunch(
        upload=upload
    )
