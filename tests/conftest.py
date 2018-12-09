import os
import pytest
import subprocess

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URI = 'postgresql://localhost/test_team_metrics'


@pytest.fixture(scope='session')
def engine():
    return create_engine(TEST_DATABASE_URI)
    # yield engine
    # engine.dispose()


@pytest.yield_fixture(scope='session')
def tables(engine):
    from team_metrics.models import Base

    try:
        import os
        Base().metadata.create_all(engine)
    except sqlalchemy.exc.OperationalError as e:
        if 'database "{}" does not exist'.format(TEST_DATABASE_URI.split('/')[-1:][0]) in str(e.orig):
            db_url = sqlalchemy.engine.url.make_url(TEST_DATABASE_URI)
            dbname = db_url.database

            if db_url.drivername == 'postgresql':
                subprocess.call(['/usr/bin/env', 'createdb', dbname])
                Base().metadata.create_all(engine)
        else:
            raise
    yield
    Base().metadata.drop_all(engine)


@pytest.yield_fixture
def dbsession(mocker, os_environ, engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""

    connection = engine.connect()

    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    mocker.patch('team_metrics.db.Session', return_value=session)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


@pytest.fixture
def os_environ():
    """
    clear os.environ, and restore it after the test runs
    """
    # for use whenever you expect code to edit environment variables
    old_env = os.environ.copy()

    class EnvironDict(dict):
        def __setitem__(self, key, value):
            assert type(value) == str
            super().__setitem__(key, value)

    os.environ = EnvironDict()
    yield
    os.environ = old_env
