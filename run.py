#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def setuplogging(level, stdout):
    logging.basicConfig(filename='boorubox.log', level=level)
    if stdout:
        import sys
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(level)
        logger = logging.getLogger()
        logger.addHandler(soh)


if __name__ == "__main__":
    setuplogging(logging.DEBUG, True)
    from flask import Flask
    app = Flask(__name__)
    from aip import make
    app.register_blueprint(make())
    app.run(debug=True)
