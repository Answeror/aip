from functools import wraps, partial
import logbook
from .log import Log, RedisPub


log = Log(__name__)


def _logtoredis(f, *args, **kargs):
    with logbook.NullHandler().applicationbound():
        with RedisPub():
            return f(*args, **kargs)


def logtoredis(f):
    return wraps(f)(partial(_logtoredis, f))


def block(f, *args, **kargs):
    try:
        from .rq import q
        from time import sleep
        job = q.enqueue(logtoredis(f), *args, **kargs)
        while job.result is None:
            sleep(0.5)
        ret = job.result
        job.cancel()
        return ret
    except:
        from concurrent.futures import ProcessPoolExecutor as Ex
        with Ex() as ex:
            future = ex.submit(logtoredis(f), *args, **kargs)
            return future.result()


def nonblock(f, *args, **kargs):
    try:
        from .rq import q
        q.enqueue(logtoredis(f), *args, **kargs)
    except:
        from multiprocessing import Process
        from functools import partial
        Process(
            target=partial(logtoredis(f), *args, **kargs),
            daemon=False,
        ).start()


def _thread_main(f, done):
    done(f())


def callback(f, done, *args, **kargs):
    from threading import Thread
    from functools import partial
    Thread(
        target=_thread_main,
        args=(partial(block, logtoredis(f), *args, **kargs), done),
        daemon=False,
    ).start()
