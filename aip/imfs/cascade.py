from .base import NameMixin


def load_ext(name, bases):
    return need_raw(
        name,
        bases,
        lambda base: base.load(name)
    )


def thumbnail_ext(name, width, height, bases):
    return need_raw(
        name,
        bases,
        lambda base: base.thumbnail(name, width, height)
    )


def mtime_ext(name, bases):
    return need_raw(
        name,
        bases,
        lambda base: base.mtime(name)
    )


def need_raw(name, bases, f):
    assert bases
    if len(bases) == 1:
        return f(bases[0])
    try:
        data = f(bases[0])
        if data is not None:
            return data
    except:
        pass
    data = load_ext(name, bases[1:])
    if data is not None:
        try:
            bases[0].save(name, data)
        except:
            pass
    return f(bases[0])


class Cascade(NameMixin):

    def __init__(self, *args):
        self.bases = args
        assert self.bases

    def _load(self, name):
        return load_ext(name, self.bases)

    def _save(self, name, data):
        for base in self.bases:
            base.save(name, data)

    def _thumbnail(self, name, width, height):
        return thumbnail_ext(name, width, height, self.bases)

    def _has(self, name):
        for base in self.bases:
            if base.has(name):
                return True
        return False

    def _remove(self, name):
        for base in self.bases:
            base.remove(name)

    def _mtime(self, name):
        return mtime_ext(name, self.bases)

    def _cache_timeout(self, name):
        for base in self.bases:
            ret = base.cache_timeout(name)
            if ret is not None:
                return ret
        return None
