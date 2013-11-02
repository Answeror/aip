import logbook
from .log import Log, RedisPub


log = Log(__name__)


def guard(f, *args, **kargs):
    with logbook.NullHandler().applicationbound():
        with RedisPub():
            try:
                return f(*args, **kargs)
            except:
                log.exception('task {} failed', f.__name__)


def block(f, *args, **kargs):
    return block_call(f, args, kargs)


def block_call(f, args=[], kargs={}, timeout=None, bound='cpu'):
    impl = {
        'cpu': cpu_bound_block_call,
        'io': io_bound_block_call,
    }.get(bound)
    assert impl, 'unknown bound type: %s' % bound
    return impl(f, args, kargs, timeout)


def nonblock(f, *args, **kargs):
    return nonblock_call(f, args, kargs)


def nonblock_call(f, args=[], kargs={}, timeout=None, bound='cpu'):
    impl = {
        'cpu': cpu_bound_nonblock_call,
        'io': io_bound_nonblock_call,
    }.get(bound)
    assert impl, 'unknown bound type: %s' % bound
    return impl(f, args, kargs, timeout)


def cpu_bound_block_call(f, args, kargs, timeout):
    try:
        from .rq import q
        from time import sleep
        job = q.enqueue_call(
            guard,
            args=[f] + list(args),
            kwargs=kargs,
            timeout=timeout,
        )
        while job.result is None:
            sleep(0.5)
        ret = job.result
        job.cancel()
        return ret
    except:
        from concurrent.futures import ProcessPoolExecutor as Ex
        with Ex() as ex:
            future = ex.submit(
                target=guard,
                args=[f] + list(args),
                kwargs=kargs,
            )
            return future.result()


def io_bound_block_call(f, args, kargs, timeout):
    from .local import thread_slave
    return thread_slave.submit(
        guard,
        args=[f] + list(args),
        kwargs=kargs,
    ).result(timeout)


def io_bound_nonblock_call(f, args, kargs, timeout):
    assert timeout is None, "thread based non-block doesn't support timeout"
    from .local import thread_slave
    return thread_slave.submit(
        guard,
        args=[f] + list(args),
        kwargs=kargs,
    )


def cpu_bound_nonblock_call(f, args, kargs, timeout):
    try:
        from .rq import q
        q.enqueue_call(
            guard,
            args=[f] + list(args),
            kwargs=kargs,
            timeout=timeout,
        )
    except:
        from multiprocessing import Process
        Process(
            target=guard,
            args=[f] + list(args),
            kwargs=kargs,
            daemon=False,
        ).start()


def _thread_main(f, done):
    done(f())


def callback(f, done, *args, **kargs):
    from threading import Thread
    from functools import partial
    Thread(
        target=_thread_main,
        args=(partial(block, guard, f, *args, **kargs), done),
        daemon=False,
    ).start()
