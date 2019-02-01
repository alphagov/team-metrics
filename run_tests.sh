#!/bin/bash
command -v psql > /dev/null || (echo "psql not installed" && NO_PSQL=1);

if [[ $NO_PSQL == 1 || $USE_DOCKER == 'true' ]]; then
    command -v docker > /dev/null || (echo "docker not installed" && exit 1)
    echo "====> creating database in docker"
    DB_CONTAINER_NAME="team-metrics-dev-postgres"
    DB_NAME="team_metrics_test"
    function stop_database {
        docker stop "$DB_CONTAINER_NAME" >/dev/null 2>&1 || echo -n ''
    }
    trap stop_database EXIT

    export SQLALCHEMY_DATABASE_URI=postgresql://postgres@localhost:5432/$DB_NAME
    stop_database
    mkdir -p log
    docker run -e POSTGRES_DB=$DB_NAME --name "$DB_CONTAINER_NAME" --rm -p 5432:5432 postgres >log/postgres.log 2>&1 &
else
    if [ -z "$SQLALCHEMY_DATABASE_URI" ]; then
        echo "Please export SQLALCHEMY_DATABASE_URI, normally postgres://localhost:5432 or 'export USE_DOCKER=true' to use docker postgres"
        exit
    fi
fi

python -m pytest --cov=app --cov-report=term-missing --disable-pytest-warnings tests/

if [ $? != '0' ]; then
    exit 1
fi
