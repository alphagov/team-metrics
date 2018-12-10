#!/usr/bin/env bash

set -eu

command -v npm > /dev/null || (echo "npm not installed" && exit 1)

if [ -z "$(command -v npm)" ]; then
    echo "you need to install npm"
    exit 1
fi

npm install --save
