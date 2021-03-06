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
        virtualenv -p /usr/local/bin/python3.6 venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
else
    pip install -r requirements.txt
fi

command -v psql > /dev/null || (echo "psql not installed" && NO_PSQL=1);

if [[ $NO_PSQL == 1 || $USE_DOCKER == 'true' ]]; then
    command -v docker > /dev/null || (echo "docker not installed" && exit 1)
    echo "====> creating database in docker"
    DB_CONTAINER_NAME="team-metrics-dev-postgres"
    function stop_database {
        docker stop "$DB_CONTAINER_NAME" >/dev/null 2>&1 || echo -n ''
    }
    trap stop_database EXIT
    
    export SQLALCHEMY_DATABASE_URI=postgresql://postgres@localhost:5432/team_metrics
    stop_database
    mkdir -p log
    docker run -e POSTGRES_DB=team_metrics --name "$DB_CONTAINER_NAME" --rm -p 5432:5432 postgres >log/postgres.log 2>&1 &
else
    if [ -z "$SQLALCHEMY_DATABASE_URI" ]; then
        echo "Please export SQLALCHEMY_DATABASE_URI, normally postgres://localhost:5432 or 'export USE_DOCKER=true' to use docker postgres"
        exit
    else
        if psql -lqt | cut -d \| -f 1 | grep -qw ${SQLALCHEMY_DATABASE_URI##*/}; then
            echo ${SQLALCHEMY_DATABASE_URI##*/} 'database found in PSQL'
        else
            createdb ${SQLALCHEMY_DATABASE_URI##*/}
            echo ${SQLALCHEMY_DATABASE_URI##*/} 'created in PSQL'
        fi
    fi
fi

echo "====> running webpack"
npx webpack

echo "====> running app"
export FLASK_APP=application.py
export FLASK_ENV=development
python -m flask run
