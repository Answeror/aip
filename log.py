#!/usr/bin/env python


from logbook import FileHandler
import logbook
import os
from aip.log import RedisSub


CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))


def main():
    try:
        from setproctitle import setproctitle
        setproctitle('aiplog')
    except:
        print('no setproctitle')

    sub = RedisSub()
    with logbook.NullHandler().applicationbound():
        with FileHandler(
            os.path.join(CURRENT_PATH, 'data', 'aip.redis.log'),
            level=logbook.INFO,
            bubble=True,
        ):
            sub.dispatch_forever()


if __name__ == '__main__':
    main()
