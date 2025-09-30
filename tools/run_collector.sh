#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python data_collector.py "$@"
else
  python3 data_collector.py "$@"
fi
