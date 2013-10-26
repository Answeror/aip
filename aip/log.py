import logging


class Meta(type):

    def __init__(self, *args, **kargs):
        type.__init__(self, *args, **kargs)
        for method in [
            'debug',
            'warning',
            'info',
            'error',
            'exception'
        ]:
            def indirect(self, *args, method=method, **kargs):
                return getattr(self.log, method)(*args, **kargs)
            indirect.__name__ = method
            setattr(self, method, indirect)


class Log(object, metaclass=Meta):

    def __init__(self, name):
        self.name = name

    @property
    def log(self):
        return logging.getLogger(__name__)
