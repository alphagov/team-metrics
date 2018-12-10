#!/usr/bin/env bash

set -e

if [ -z $(command -v npm) ]; then
    echo "you need to install npm"
    exit 1
fi

npm install --save
