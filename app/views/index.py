import json
import os

from flask import Blueprint, redirect, request, session, url_for
from requests_oauthlib import OAuth2Session
import requests
from requests.exceptions import HTTPError

from app.config import (
    AUTH_URI,
    CLIENT_ID,
    CLIENT_SECRET,
    DEFAULT_PATH,
    OAUTHLIB_INSECURE_TRANSPORT,
    REDIRECT_URI,
    REVOKE_URI,
    SCOPE,
    TOKEN_URI,
    USER_INFO,
    TEAM_PROFILES,
)
from app.views import env
index_blueprint = Blueprint('/', __name__)


@index_blueprint.route('/', methods=['GET'])
def index():
    if session.get('email'):
        path = _get_user_from_team(session['email'])

        if not path:
            return redirect(f'teams/{DEFAULT_PATH}')
        else:
            return redirect(f'teams/{path}')

    google = _get_google_auth()
    auth_url, state = google.authorization_url(AUTH_URI, access_type='offline')
    session['oauth_state'] = state

    template = env.get_template('index.html')
    return template.render(auth_url=auth_url)


@index_blueprint.route('/oauth2callback')
def callback():
    # to allow for http://localhost callback
    if OAUTHLIB_INSECURE_TRANSPORT:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Redirect user to home page if already logged in.

    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'

    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        # Execution reaches here when user has successfully authenticated our app.
        google = _get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(TOKEN_URI, client_secret=CLIENT_SECRET, authorization_response=request.url)
            session['oauth_token'] = token
        except HTTPError:
            return 'HTTPError occurred.'
        google = _get_google_auth(token=token)
        resp = google.get(USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            session['email'] = email

            if session.get('target_url'):
                return redirect(session.pop('target_url'))
            else:
                path = _get_user_from_team(email)
                if not path:
                    return redirect(f'teams/{DEFAULT_PATH}')
                else:
                    return redirect(f'teams/{path}')
        return 'Could not fetch your information.'


@index_blueprint.route('/logout')
def logout():
    del session['email']
    requests.post(
        REVOKE_URI,
        params={'token': session.pop('oauth_token')},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )

    return redirect(url_for('.index'))


def _get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(CLIENT_ID, token=token)
    if state:
        return OAuth2Session(CLIENT_ID, state=state, redirect_uri=REDIRECT_URI)
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    return oauth


def _get_user_from_team(email):
    _user = email.split('@')[0]
    for team in TEAM_PROFILES:
        for user in team['users'].split(' '):
            if user == _user:
                return team['path']
