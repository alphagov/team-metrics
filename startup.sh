#!/usr/bin/env bash

set -e

if [ ! -d node_modules ]; then
    echo "====> installing frontend assets"
    ./install-frontend-assets.sh
fi

if [ -z "$VIRTUAL_ENV" ]; then
    if [ ! -d venv ]; then
        echo "====> did not detect virtualenv, installing..."
        # use pip3 to install virtualenv, and use pip later because it's the right one at that point
        pip3 install virtualenv
        virtualenv -p /usr/local/bin/python3.7 venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
else
    pip install -r requirements.txt
fi

command -v docker > /dev/null || (echo "docker not installed" && exit 1)
echo "====> starting database"
DB_CONTAINER_NAME="team-metrics-dev-postgres"
export PYTHONPATH=$(pwd)

function stop_database {
    docker stop "$DB_CONTAINER_NAME" >/dev/null 2>&1 || echo -n ''
}
trap stop_database EXIT

stop_database
mkdir -p log
docker run -e POSTGRES_DB=team_metrics --name "$DB_CONTAINER_NAME" --rm -p 5432:5432 postgres >log/postgres.log 2>&1 &

# TODO: find a better way of checking the database is up
sleep 5

export SQLALCHEMY_DATABASE_URI=postgres://postgres@localhost:5432/team_metrics
alembic revision --autogenerate
alembic upgrade head

echo "====> running webpack"
npx webpack

echo "====> running app"
export FLASK_APP=application.py
export FLASK_ENV=development
python -m flask run
