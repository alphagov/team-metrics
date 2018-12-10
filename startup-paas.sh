#!/bin/bash

set -e -o pipefail

TERMINATE_TIMEOUT=9

function start_application {
  exec "$@" &
  APP_PID=`jobs -p`
  echo "Application process pid: ${APP_PID}"
}

# The application has to start first!
start_application "$@"
