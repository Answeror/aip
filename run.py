#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from aip.config import AIP_LOG_FILE_PATH


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
    logging.basicConfig(filename=AIP_LOG_FILE_PATH, level=level)
    if stdout:
        import sys
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(level)
        logger = logging.getLogger()
        logger.addHandler(soh)


AIP_TEMP_PATH = os.path.abspath('temp')
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % os.path.abspath(os.path.join('temp', 'aip.db'))


if __name__ == "__main__":
    setuplogging(logging.DEBUG, True)
    from aip import make
    app = make(__name__)
    app.secret_key = 'why would I tell you my secret key?'
    app.run(debug=True)
