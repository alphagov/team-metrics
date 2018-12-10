#!/usr/bin/env bash

set -e

if [ ! -d node_modules ]; then
    echo "====> installing frontend assets"
    ./install-frontend-assets.sh
fi

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

echo "====> running webpack"
npx webpack

echo "====> running app"
export FLASK_APP=application.py
export FLASK_ENV=development
python -m flask run
