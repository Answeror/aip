#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from .settings import IMAGE_CACHE_TIMEOUT
from datetime import datetime
from . import app as aip, views
from .cache import cached


aip.route('/', defaults={'page': 1})(views.posts)
aip.route('/page/<int:page>')(views.posts)
aip.route('/sample/<md5>')(cached(IMAGE_CACHE_TIMEOUT)(views.sample))
aip.route('/update', defaults={'begin': datetime.today().strftime('%Y%m%d')})(views.update)
aip.route('/update/<begin>')(views.update)
aip.route('/image_count')(views.image_count)
aip.route('/user_count')(views.user_count)
aip.route('/unique_image_count')(views.unique_image_count)
aip.route('/unique_image_md5')(views.unique_image_md5)
aip.route('/update_images', defaults={'begin': datetime.today().strftime('%Y%m%d')})(views.update_images)
aip.route('/update_images/<begin>')(views.update_images)
aip.route('/last_update_time')(views.last_update_time)
aip.route('/style.css')(views.style)
aip.route('/log')(views.log)
aip.route('/clear')(views.clear)
aip.route('/login', methods=['GET', 'POST'])(views.login)
aip.route('/create_profile', methods=['GET', 'POST'])(views.create_profile)
aip.route('/logout')(views.logout)
