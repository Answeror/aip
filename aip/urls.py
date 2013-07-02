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
    aip.route('/site_count')(views.site_count)
    aip.route('/update_sites')(views.update_sites)
    aip.route('/image_count')(views.image_count)
    aip.route('/update_images', defaults={'begin': datetime.today().strftime('%Y%m%d')})(views.update_images)
    aip.route('/update_images/<begin>')(views.update_images)
    aip.route('/last_update_time')(views.last_update_time)
    aip.route('/style.css')(views.style)
