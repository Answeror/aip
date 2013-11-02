from ..work import nonblock_call


class AsyncSave(object):

    def __init__(self, base):
        self.base = base

    def save(self, name, data):
        return nonblock_call(
            self.base.save,
            args=[name, data],
            bound='io'
        )

    def __getattr__(self, name):
        return getattr(self.base, name)


def asyncsave(base):
    return AsyncSave(base)
