def block(f, *args, **kargs):
    try:
        from .rq import q
        from time import sleep
        job = q.enqueue(f, *args, **kargs)
        while job.result is None:
            sleep(0.5)
        ret = job.result
        job.cancel()
        return ret
    except:
        return f(*args, **kargs)


def nonblock(f, *args, **kargs):
    try:
        from .rq import q
        q.enqueue(f, *args, **kargs)
    except:
        return f(*args, **kargs)
