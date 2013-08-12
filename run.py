#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import json


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


AIP_TEMP_PATH = os.path.abspath('temp')
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % os.path.abspath(os.path.join(AIP_TEMP_PATH, 'aip.db'))
#SQLALCHEMY_DATABASE_URI = 'sqlite://'
PROFILE = False
SQLALCHEMY_RECORD_QUERIES = False
DATABASE_QUERY_TIMEOUT = 1e-5
AIP_LOG_FILE_PATH = os.path.join(AIP_TEMP_PATH, 'aip.log')

AIP_IMGUR_RETRY_LIMIT = 3
with open(os.path.join(os.path.dirname(__file__), 'imgur.json'), 'rb') as f:
    imgur_conf = json.loads(f.read().decode('ascii'))
    AIP_IMGUR_CLIENT_IDS = imgur_conf['client_ids']
    AIP_IMGUR_ALBUM_ID = imgur_conf['album']['id']
    AIP_IMGUR_ALBUM_DELETEHASH = imgur_conf['album']['deletehash']


def setuplogging(level, stdout):
    logging.basicConfig(filename=AIP_LOG_FILE_PATH, level=level)
    if stdout:
        import sys
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(level)
        logger = logging.getLogger()
        logger.addHandler(soh)


if __name__ == "__main__":
    setuplogging(logging.DEBUG, True)
    from aip import make
    app = make(__name__)
    app.secret_key = 'why would I tell you my secret key?'
    if app.config['PROFILE']:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])  # , sort_by=('cumulative', 'calls'))
    app.run('0.0.0.0', debug=True, threaded=True)
