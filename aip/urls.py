#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def make(aip):
    from datetime import datetime
    from . import views
    aip.route('/', defaults={'page': 1})(views.posts)
    aip.route('/page/<int:page>')(views.posts)
    aip.route('/image/<path:src>')(views.image)
    aip.route('/update', defaults={'begin': datetime.today().strftime('%Y%m%d')})(views.update)
    aip.route('/update/<begin>')(views.update)
