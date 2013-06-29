#!/usr/bin/env python
# -*- coding: utf-8 -*-


def danbooru_ctime(s):
    from datetime import datetime
    return datetime.utcfromtimestamp(int(s))


providers = [
    {
        'key': 'yande.re',
        'name': 'yande.re',
        'type': 'danbooru',
        'url': 'https://yande.re',
        'mapping': {
            'url': 'file_url',
            'ctime': ('created_at', danbooru_ctime),
            'tags': lambda s: s.split(' ')
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
            'tags': lambda s: s.split(' ')
        }
    }
]
