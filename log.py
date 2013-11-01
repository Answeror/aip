#!/usr/bin/env python


from logbook import TimedRotatingFileHandler
import logbook
import os
from aip.log import RedisSub


CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))


def path(filename):
    return os.path.join(CURRENT_PATH, 'data', filename)


def handle(level):
    return TimedRotatingFileHandler(
        path('aip.%s.log' % level),
        date_format='%Y-%m-%d',
        level=getattr(logbook, level.upper()),
        bubble=True,
    )


def main():
    try:
        from setproctitle import setproctitle
        setproctitle('aiplog')
    except:
        print('no setproctitle')

    sub = RedisSub()
    with logbook.NullHandler().applicationbound():
        with handle('debug'):
            with handle('info'):
                with handle('error'):
                    sub.dispatch_forever()


if __name__ == '__main__':
    main()
