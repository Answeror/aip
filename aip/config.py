#!/usr/bin/env python
# -*- coding: utf-8 -*-


AIP_PER = 32
AIP_COLUMN_WIDTH = 200
AIP_GUTTER = 10
AIP_LOG_FILE_PATH = 'aip.log'
AIP_IMAGE_CACHE_TIMEOUT = 60 * 60 * 24
AIP_SAMPLE_WIDTH = 480
AIP_RESOLUTION_LEVEL = 1.618
AIP_UPLOAD_IMGUR_RETRY_LIMIT = 0
AIP_LOADING_TIMEOUT = 3600
AIP_PROXIED_TIMEOUT = 10
AIP_REPROXY_LIMIT = 1
AIP_REPROXY_INTERVAL = 5
AIP_RELOAD_LIMIT = 0
AIP_RELOAD_INTERVAL = 1
AIP_UPLOAD_IMGUR_TIMEOUT = 30
AIP_IMGUR_RESIZE_LIMIT = 1024
AIP_IMMIO_RESIZE_MAX_SIZE = (640, 480)
AIP_UPLOAD_IMMIO_TIMEOUT = 30
AIP_SLAVE_COUNT = 3
AIP_EVENT_QUEUE_MAX_LENGTH = 65536
AIP_PUMP_INTERVAL = 1
AIP_STREAM_TIMEOUT = 30
AIP_STREAM_EVENT_TIMEOUT = 10
AIP_STREAM_HELLO_LIMIT = 3
AIP_META_DAG = 'dag'
AIP_TAG_SHORT_NAME_LIMIT = 16
AIP_RANK_PLUS = -1
AIP_RANK_MINUS = -1

AIP_DETAIL_LOADING_TIMEOUT = 3600
AIP_DETAIL_RELOAD_LIMIT = 0
AIP_DETAIL_RELOAD_INTERVAL = 10

AIP_TIMESTAMPED_TIMEOUT = 60 * 60 * 24
AIP_TIMESTAMP_FIELD = 'ts'

AIP_PULLING_THRESHOLD = 16
AIP_FADEOUT_TIMEOUT = 60
AIP_PULLING_INTERVAL = 2

AIP_BAIDUPAN_TIMEOUT = 300
AIP_UPDATE_TIMEOUT = 600

try:
    import pkg_resources
    AIP_VERSION = pkg_resources.require('aip.core')[0].version
except:
    AIP_VERSION = '0.1.0'
