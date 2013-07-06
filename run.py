#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask
import logging
from aip import make
from aip.settings import LOG_FILE_PATH
from aip.stores import sqlalchemy
from flask.ext.sqlalchemy import SQLAlchemy


def setuplogging(level, stdout):
    logging.basicConfig(filename=LOG_FILE_PATH, level=level)
    if stdout:
        import sys
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(level)
        logger = logging.getLogger()
        logger.addHandler(soh)


if __name__ == "__main__":
    setuplogging(logging.DEBUG, True)
    app = Flask(__name__)
    root = os.path.dirname(__file__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % os.path.join(root, 'temp', 'aip.db')
    db = SQLAlchemy(app)
    aip = make()
    aip.store = sqlalchemy.make(db)
    app.register_blueprint(aip)
    db.create_all()
    app.run(debug=True)
