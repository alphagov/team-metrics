#!/usr/bin/env bash

set -e

# use pip3 to install virtualenv, and use pip later because it's the right one at that point
pip3 install virtualenv
virtualenv -p /usr/local/bin/python3.7 venv
source venv/bin/activate

pip install -r requirements.txt
