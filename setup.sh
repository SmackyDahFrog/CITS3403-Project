#!/usr/bin/env bash
#one-shot setup for macOS, Linux and WSL
set -e

if ! command -v python3 >/dev/null; then
    echo "python3 not found - install Python 3.10+ first"
    exit 1
fi

# create venv on first run only
if [ ! -d venv ]; then
    python3 -m venv venv
fi

#  install pinned dependencies from requirements.txt
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

# apply schema migration to build app/user.db
FLASK_APP=run.py ./venv/bin/flask db upgrade

echo ""
echo "Setup complete."
echo ""
echo "Activate the venv:   source venv/bin/activate"
echo "Start the server:    python run.py"
echo "Run the tests:       python -m unittest tests.test_auth"
echo "Reset the database:  rm app/user.db && flask db upgrade"
