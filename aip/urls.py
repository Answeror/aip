#!/usr/bin/env python
# -*- coding: utf-8 -*-


from . import views, aip


aip.route('/', defaults={'page': 1})(views.posts)
aip.route('/page/<int:page>')(views.posts)
aip.route('/image/<path:src>')(views.image)
aip.route('/update')(views.update)
