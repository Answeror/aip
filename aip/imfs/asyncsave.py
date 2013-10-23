from ..async import nonblock


class AsyncSave(object):

    def __init__(self, base):
        self.base = base

    def save(self, name, data):
        return nonblock(self.base.save, name, data)

    def __getattr__(self, name):
        return getattr(self.base, name)


def asyncsave(base):
    return AsyncSave(base)
