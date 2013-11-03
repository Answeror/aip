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


def nonblock_call(f, args=[], kargs={}, timeout=None, bound='cpu', group=None):
    if group is None:
        impl = {
            'cpu': cpu_bound_nonblock_call,
            'io': io_bound_nonblock_call,
        }.get(bound)
        assert impl, 'unknown bound type: %s' % bound
        return impl(f, args, kargs, timeout)

    if bound == 'cpu':
        log.warning(
            'task assigned to group "{}", bound type fall back to "io"',
            group
        )
    assert timeout is not None, 'group task must have timeout setting'

    from .local import core
    from flask import current_app
    from redis import Redis
    redis = Redis()
    run_group_app_task(
        redis,
        ':'.join([core.group_app_task_key, group, 'lock']),
        group,
        current_app.kargs,
        timeout
    )
    import pickle
    redis.rpush(
        ':'.join([core.group_app_task_key, group]),
        pickle.dumps((f, args, kargs))
    )


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
            future = ex.submit(guard, f, *args, **kargs)
            return future.result()


def io_bound_block_call(f, args, kargs, timeout):
    from .local import thread_slave
    return thread_slave.submit(guard, f, *args, **kargs).result(timeout)


def io_bound_nonblock_call(f, args, kargs, timeout):
    assert timeout is None, "thread based non-block doesn't support timeout"
    from .local import thread_slave
    return thread_slave.submit(guard, f, *args, **kargs)


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


def group_app_task(redis, name, appops, timeout):
    log.debug('group app task {} start', name)
    import pickle
    from flask import copy_current_request_context
    from . import make_slave_app
    from .local import core
    app = make_slave_app(appops)
    while True:
        message = redis.blpop(
            ':'.join([core.group_app_task_key, name]),
            timeout=timeout
        )
        if message is None:
            break
        task, args, kargs = pickle.loads(message[1])
        try:
            with app.test_request_context():
                nonblock_call(
                    copy_current_request_context(task),
                    args=args,
                    kargs=kargs,
                    bound='io',
                )
        except:
            log.exception('group task {} failed', task.__name__)
    log.debug('group app task {} done', name)


def group_app_task_out(lock, name, appops, timeout):
    from redis import Redis
    redis = Redis()
    try:
        group_app_task(redis, name, appops, timeout)
    finally:
        redis.delete(lock)


def run_group_app_task(redis, lock, name, appops, timeout):
    from .local import core
    from uuid import uuid4
    ts = str(uuid4()).encode('ascii')
    if not redis.setnx(lock, ts):
        return
    try:
        nonblock_call(
            group_app_task_out,
            kargs=dict(
                lock=lock,
                name=name,
                appops=appops,
                timeout=timeout,
            ),
            bound='cpu',
            timeout=core.group_app_task_timeout,
        )
    except:
        redis.delete(lock)
        raise
