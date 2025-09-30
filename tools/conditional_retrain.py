#!/usr/bin/env python3
"""Conditional retrain helper.

Checks labeled_activities count and compares to the last retrain manifest.
If enough new labels exist (or total labels exceed a minimum), runs export -> retrain -> archive.

Usage: python conditional_retrain.py [--min-total N] [--min-new N] [--archive]
"""
import sqlite3
import os
import argparse
import joblib
import glob
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'productivity_agent.db'
MODELS_DIR = ROOT / 'models'


def get_total_labels():
    if not DB_PATH.exists():
        return 0
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM labeled_activities')
        return cur.fetchone()[0]
    finally:
        conn.close()


def get_last_manifest_num_labels():
    if not MODELS_DIR.exists():
        return 0
    manifests = sorted(MODELS_DIR.glob('manifest_*.joblib'), reverse=True)
    if not manifests:
        return 0
    try:
        manifest = joblib.load(manifests[0])
        return int(manifest.get('num_labels', 0))
    except Exception:
        return 0


def run_command(cmd_list):
    print('Running:', ' '.join(cmd_list))
    res = subprocess.run(cmd_list, cwd=str(ROOT))
    return res.returncode


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--min-total', type=int, default=20, help='Minimum total labeled rows to ever retrain')
    p.add_argument('--min-new', type=int, default=10, help='Minimum new labels since last retrain to trigger retrain')
    p.add_argument('--archive', action='store_true', help='Run export and archive in addition to retrain')
    args = p.parse_args()

    total = get_total_labels()
    last = get_last_manifest_num_labels()
    new_since = total - last

    print(f'Total labeled activities: {total}')
    print(f'Last retrain labeled count: {last}')
    print(f'New labels since last retrain: {new_since}')

    if total < args.min_total:
        print(f'Not enough total labeled data (need {args.min_total}). Skipping retrain.')
        return 0

    if new_since < args.min_new:
        print(f'Not enough new labels since last retrain (need {args.min_new}). Skipping retrain.')
        return 0

    # run export if requested
    python = str(ROOT / '.venv' / 'Scripts' / 'python.exe')
    if not Path(python).exists():
        python = 'python'

    if args.archive:
        rc = run_command([python, str(ROOT / 'export_dataset.py')])
        if rc != 0:
            print('Export failed, aborting retrain.')
            return rc

    # retrain and version
    rc = run_command([python, str(ROOT / 'retrain_and_version.py')])
    if rc != 0:
        print('Retrain failed.')
        return rc

    if args.archive:
        rc = run_command([python, str(ROOT / 'archive_dataset.py')])
        if rc != 0:
            print('Archive failed (non-critical).')

    print('Retrain completed successfully.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
