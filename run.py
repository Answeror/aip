#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from logbook.compat import redirect_logging
redirect_logging()

import os


if __name__ == "__main__":
    from aip import make
    from aip.log import RedisPub

    with RedisPub():
        app = make(
            instance_path=os.path.join(os.path.dirname(__file__), 'data'),
            instance_relative_config=True
        )
        app.run('0.0.0.0', debug=True, threaded=True)
