from flask import (
    redirect,
    url_for,
    request,
    render_template,
    current_app,
)
import urllib.parse
import requests
from ..local import core


def make(app, admin):

    @admin.route('/baidupcs')
    def baidupcs():
        return redirect('?'.join([
            'https://openapi.baidu.com/oauth/2.0/authorize',
            urllib.parse.urlencode(dict(
                response_type='code',
                client_id=current_app.config['AIP_BAIDUPCS_CLIENT_ID'],
                redirect_uri=url_for('.baidupcs_redirect', _external=True),
                scope='netdisk',
                display='popup',
            )),
        ]))

    @admin.route('/baidupcs/redirect')
    def baidupcs_redirect():
        code = request.args['code']
        r = requests.post(
            'https://openapi.baidu.com/oauth/2.0/token',
            params=dict(
                grant_type='authorization_code',
                code=code,
                client_id=current_app.config['AIP_BAIDUPCS_CLIENT_ID'],
                client_secret=current_app.config['AIP_BAIDUPCS_CLIENT_SECRET'],
                redirect_uri=url_for('.baidupcs_redirect', _external=True),
            )
        )
        try:
            if r.ok:
                d = r.json()
                core.set_baidupcs_access_token(
                    d['access_token'],
                    session=core.db.session,
                )
                core.set_baidupcs_refresh_token(
                    d['refresh_token'],
                    session=core.db.session,
                )
                core.db.session.commit()
                return render_template(
                    'baidupcs_redirect.html',
                    message='done'
                )
            else:
                try:
                    d = r.json()
                except:
                    raise Exception('bad response: {}'.format(r.status_code))
                else:
                    raise Exception('bad response: {}'.format(d))
        except Exception as e:
            return render_template(
                'baidupcs_redirect.html',
                message=str(e)
            )

    @admin.route('/test')
    def test():
        return render_template(
            'baidupcs_redirect.html',
            message='test page'
        )
