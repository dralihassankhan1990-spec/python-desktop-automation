#!/usr/bin/env bash
# PDF Status Report Generator — launcher (macOS / Linux)
# Usage: ./run.sh [--project ERP-01]
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
python make_sample_data.py
python generate_report.py "$@"
