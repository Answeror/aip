#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
os.environ['PYTHON_EGG_CACHE'] = DATA_PATH

with open(os.path.join(DATA_PATH, 'virtualenv'), 'rb') as f:
    virtualenv_path = f.read().strip().decode('utf-8')

if sys.platform.startswith('win'):
    mid = 'Scripts'
else:
    mid = 'bin'
activate_this = os.path.join(virtualenv_path, mid, 'activate_this.py')
exec(compile(open(activate_this).read(), activate_this, 'exec'), dict(__file__=activate_this))
sys.path.insert(0, os.path.dirname(__file__))


from logbook.compat import redirect_logging
redirect_logging()

from aip import make
from aip.log import RedisPub

with RedisPub():
    application = make(
        instance_path=DATA_PATH,
        instance_relative_config=True
    )
