from ..work import nonblock_call
from .error import ConnectionError
from ..log import Log


log = Log(__name__)


class AsyncSave(object):

    def __init__(self, base):
        self.base = base

    def save(self, name, data):
        try:
            nonblock_call(
                self.base.save,
                args=[name, data],
                bound='io'
            )
        except ConnectionError:
            log.error(
                ''.join([
                    'save {} to baidupan failed, ',
                    'due to connection error',
                ]),
                name
            )

    def __getattr__(self, name):
        return getattr(self.base, name)


def asyncsave(base):
    return AsyncSave(base)
