#!/usr/bin/env bash
# Folder Watcher & Auto-Backup — launcher (macOS / Linux)
# Usage: ./run.sh [--duration 120]   (Ctrl+C stops and writes the report)
set -e
cd "$(dirname "$0")"
exec python3 watcher.py "$@"
