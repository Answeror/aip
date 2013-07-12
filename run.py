#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from aip.settings import LOG_FILE_PATH
from aip.stores import sqlalchemy
from flask.ext.sqlalchemy import SQLAlchemy


if False:
    from aip.sources.booru import Source
    fetch = Source._fetch
    memo = {}

    def wrap(self, url):
        r = fetch(self, url)
        memo[url] = r.data
        import pickle
        with open('requests.pkl', 'wb') as f:
            pickle.dump(memo, f)
        return r

    Source._fetch = wrap


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
    from aip import app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % os.path.abspath(os.path.join('temp', 'aip.db'))
    app.config['aip.temp_path'] = os.path.abspath('temp')
    app.secret_key = 'why would I tell you my secret key?'
    db = SQLAlchemy(app)
    app.config['aip.store'] = sqlalchemy.make(db)
    db.create_all()
    app.run(debug=True)
