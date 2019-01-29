#!/bin/bash
FROM python:3.6

WORKDIR /docker_app

COPY requirements.txt .
COPY requirements_for_tests.txt .

RUN pip install -r requirements_for_tests.txt

COPY application.py .
COPY app app
COPY migrations migrations
COPY tests tests
COPY run_tests.sh .
COPY gunicorn_config.py .
COPY LICENSE .
COPY alembic.ini .
COPY pytest.ini .
COPY teams.yml .
COPY org-structure.yml .

ENV FLASK_ENV="docker"

ENTRYPOINT [ "./run_tests.sh"]
