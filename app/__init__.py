import os
import uuid

import alembic.config
from alembic.config import Config
import alembic.command
from psycopg2 import ProgrammingError

from app.metrics_db import Metrics_DB

import logging

db = Metrics_DB()


def create_app(application):
    logging.basicConfig(level=logging.DEBUG)
    handler = logging.FileHandler('log/app.log')  # errors logged to this file
    handler.setLevel(logging.DEBUG)  # only log errors and above
    application.logger.addHandler(handler)  # attach the handler to the app's logger

    db.init()
    alembic_upgrade()

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
    from app.views.cyber_team import cyber_team_blueprint
    from app.views.re_programme import re_programme_blueprint
    from app.views.techops_team import techop_team_blueprint
    from app.views.assets import assets_blueprint
    from app.views.team_metrics import team_metrics_blueprint

    application.register_blueprint(index_blueprint)
    application.register_blueprint(cyber_team_blueprint)
    application.register_blueprint(re_programme_blueprint)
    application.register_blueprint(techop_team_blueprint)
    application.register_blueprint(assets_blueprint)
    application.register_blueprint(team_metrics_blueprint)
