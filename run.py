#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os


if __name__ == "__main__":
    from aip import make
    app = make(
        instance_path=os.path.join(os.path.dirname(__file__), 'data'),
        instance_relative_config=True
    )
    app.run('0.0.0.0', debug=True, threaded=True)
