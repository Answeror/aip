import hashlib


def md5(data):
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()