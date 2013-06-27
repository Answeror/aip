#!/usr/bin/env python
# -*- coding: utf-8 -*-


from . import views, app


app.route('/', defaults={'page': 1})(views.posts)
app.route('/page/<int:page>')(views.posts)
app.route('/image/<id>')(views.image)
