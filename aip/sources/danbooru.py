#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
from urllib.parse import urljoin
from . import booru


class Source(booru.Source):

    def __init__(self, make_image):
        super(Source, self).__init__(make_image)

    @property
    def start_page(self):
        return 1

    @property
    def nsfw_tag(self):
        return "rating:s"

    @property
    def image_url_template(self):
        return urljoin(
            self.url,
            "/post/index.json?tags=%s&limit=%s&page=%s"
        )

    @property
    def tag_url_template(self):
        return urljoin(
            self.url,
            "/tags/index.json?limit=%s&page=%s"
        )

    def parse(self, response):
        return json.loads(response.data.decode('utf-8'))
