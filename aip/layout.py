from flask import render_template, g
import pickle
from datetime import datetime


def render_layout(*args, **kargs):
    t = g.last_update_time
    t = datetime(year=1970, month=1, day=1) if t is None else pickle.loads(t)
    return render_template(
        *args,
        last_update_time=t,
        entry_count=g.entry_count,
        user_count=g.user_count,
        **kargs
    )
