#!/bin/sh
set -eu
cd "$(dirname "$0")"
PYTHON_BIN="${FRUITFLY_PYTHON:-python3}"
"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python run.py "$@"
