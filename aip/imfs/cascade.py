from .base import NameMixin


def load_ext(name, bases):
    assert bases
    if len(bases) == 1:
        return bases[0].load(name)
    try:
        data = bases[0].load(name)
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
    return data


def thumbnail_ext(name, width, height, bases):
    assert bases
    if len(bases) == 1:
        return bases[0].thumbnail(name, width, height)
    try:
        data = bases[0].thumbnail(name, width, height)
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
    return bases[0].thumbnail(name, width, height)


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
