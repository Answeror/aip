from flask import render_template, g
import pickle


def render_layout(*args, **kargs):
    t = g.last_update_time
    t = '' if t is None else pickle.loads(t).strftime('%Y-%m-%d %H:%M:%S')
    return render_template(
        *args,
        last_update_time=t,
        **kargs
    )
