try:
    from .rq import q
    HASRQ = True
except:
    HASRQ = False


class AsyncSave(object):

    def __init__(self, base):
        self.base = base

    def save(self, name, data):
        if HASRQ:
            q.enqueue(self.base.save, name, data)
        else:
            return self.base.save(name, data)

    def __getattr__(self, name):
        return getattr(self.base, name)


def asyncsave(base):
    return AsyncSave(base)
