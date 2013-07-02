#!/usr/bin/env python
# -*- coding: utf-8 -*-


def yandere_ctime(s):
    from datetime import datetime
    return datetime.utcfromtimestamp(int(s))


def danbooru_ctime(s):
    from datetime import datetime
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


providers = [
    {
        'key': 'yande.re',
        'name': 'yande.re',
        'type': 'danbooru',
        'url': 'https://yande.re',
        'mapping': {
            'url': 'file_url',
            'ctime': ('created_at', yandere_ctime),
            'tags': lambda s: s.replace(' ', ';'),
            'width': int,
            'height': int,
            'score': int,
            'post_url': ('id', lambda s: '/post/view/{}'.format(s))
        }
    },
    {
        'key': 'danbooru.donmai.us',
        'name': 'danbooru.donmai.us',
        'type': 'danbooru',
        'url': 'http://danbooru.donmai.us',
        'mapping': {
            'url': 'file_url',
            'ctime': ('created_at', danbooru_ctime),
            'tags': lambda s: s.replace(' ', ';'),
            'width': int,
            'height': int,
            'score': int,
            'post_url': ('id', lambda s: '/posts/{}'.format(s))
            #'sample_url': ('md5', lambda s: '/data/sample/sample-{}.jpg'.format(s))
        }
    }
]
