class ImfsError(Exception):
    pass


class NotFoundError(ImfsError):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '%s not found' % self.name


class ConnectionError(ImfsError):
    pass
