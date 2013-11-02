def make(app):
    from flask import Blueprint
    admin = Blueprint(
        'admin',
        __name__
    )
    from . import views
    views.make(app, admin)
    app.register_blueprint(admin, url_prefix='/admin')
