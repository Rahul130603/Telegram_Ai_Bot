#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
test -x .venv/bin/python || { echo "Run scripts/setup.sh first"; exit 1; }
exec .venv/bin/python -m app

