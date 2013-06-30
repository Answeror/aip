"""
Initialize Flask app

"""
from flask import Flask

# from flask_debugtoolbar import DebugToolbarExtension
from gae_mini_profiler import profiler, templatetags
from werkzeug.debug import DebuggedApplication


app = Flask('application')
app.config.from_object('application.settings')

from aip import aip
from . import store
aip.store = store
app.register_blueprint(aip)

# Enable jinja2 loop controls extension
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

@app.context_processor
def inject_profiler():
    return dict(profiler_includes=templatetags.profiler_includes())

# Pull in URL dispatch routes
#import urls

# Flask-DebugToolbar (only enabled when DEBUG=True)
# toolbar = DebugToolbarExtension(app)

# Werkzeug Debugger (only enabled when DEBUG=True)
if app.debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

# GAE Mini Profiler (only enabled on dev server)
app = profiler.ProfilerWSGIMiddleware(app)
