#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
test -d .venv || python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.txt
test -f .env || cp .env.example .env
echo "Setup complete. Fill backend/.env privately, then run scripts/run.sh"

