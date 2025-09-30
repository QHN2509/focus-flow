#!/usr/bin/env bash
# Run the daily report from the project root using the project's venv if present
cd "$(dirname "$0")/.." || exit 1
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python run_agent.py "$@"
else
  python3 run_agent.py "$@"
fi
