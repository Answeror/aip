import time
import json
import requests
import http.cookies
from ..log import Log
import urllib.parse


log = Log(__name__)


def parse_json(raw):
    try:
        data = json.loads(raw)
    except:
        try:
            data = eval(
                raw,
                type("Dummy", (dict,), dict(__getitem__=lambda s, n: n))()
            )
        except:
            data = {}
    return data


def timestamp():
    return int(time.time() * 1000)


class BaiduPan(object):

    def __init__(self, cookies):
        self.session = requests.Session()
        self.session.headers.update({
            'User-agent': ''.join([
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.4',
                '(KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4',
            ])
        })
        c = http.cookies.SimpleCookie()
        c.load(cookies)
        self.session.cookies.update(c)

    def raw_uri(self, md5):
        try:
            ret = parse_json(self.session.get(
                'http://pan.baidu.com/api/search',
                params=dict(
                    channel='chunlei',
                    clienttype=0,
                    web=1,
                    t=timestamp(),
                    key=md5,
                    dir='/apps/aip/cache',
                )
            ).content.decode('utf-8'))
        except:
            log.exception('get uri of {} failed', md5)
            return None

        return parse_response(ret, md5)

    def redirected_uri(self, md5):
        uri = self.raw_uri(md5)
        if uri:
            r = self.session.get(uri)
            parts = list(urllib.parse.urlparse(r.url))
            parts[1] = 'www.baidupcs.com'
            return urllib.parse.urlunparse(parts)

    def uri(self, md5):
        uri = self.redirected_uri(md5)
        if uri:
            return uri.replace('http://', '//')


def parse_response(r, md5):
    if 'list' not in r:
        log.error('get uri of {} failed, response: {}', md5, r)

    if not r['list']:
        return None

    try:
        return r['list'][0]['dlink']
    except:
        log.exception('get uri of {} failed, response: {}', md5, r)
        return None
