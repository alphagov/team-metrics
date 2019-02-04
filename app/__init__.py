import os
import uuid

import alembic.config
from alembic.config import Config
import alembic.command
from flask import redirect, request, session
from flask import Flask
from psycopg2 import ProgrammingError
import requests

from app.metrics_db import Metrics_DB

import logging

db = Metrics_DB()


def create_app(application):
    logging.basicConfig(level=logging.DEBUG)
    handler = logging.FileHandler('log/app.log')  # errors logged to this file
    handler.setLevel(logging.DEBUG)  # only log errors and above
    application.logger.addHandler(handler)  # attach the handler to the app's logger

    from app.config import Config
    application.config.from_object(Config)

    db.init()
    alembic_upgrade()

    application.before_request(check_auth_before_request)

    register_blueprint(application)

    return application


def alembic_upgrade():
    config = Config('alembic.ini')
    config.attributes['configure_logger'] = False

    try:
        alembic.command.upgrade(config, 'head')
    except ProgrammingError as e:
        logging.error('post upgrade exception')
        raise RuntimeError(e)


def register_blueprint(application):
    from app.views.index import index_blueprint
    from app.views.assets import assets_blueprint
    from app.views.team_metrics import team_metrics_blueprint

    application.register_blueprint(index_blueprint)
    application.register_blueprint(assets_blueprint)
    application.register_blueprint(team_metrics_blueprint)


def check_auth_before_request():
    if '/teams/' in request.url and not session.get('email'):
        session['target_url'] = request.url
        return redirect('/')
