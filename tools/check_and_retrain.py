#!/usr/bin/env python3
"""
Check labeled_activities counts and run export/retrain/archive only when thresholds are met.

Usage (called by wrapper CMD):
  python tools/check_and_retrain.py [--min-total N] [--min-new M] [--force]

Defaults: min_total=20, min_new=10
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import glob
import joblib
import os
from datetime import timedelta


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "productivity_agent.db"
MODELS_DIR = ROOT / "models"
LOGS_DIR = ROOT / "tools" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def prune_old_logs(logs_dir: Path, keep_days: int = 30) -> None:
    """Remove log files older than keep_days to avoid unbounded growth."""
    cutoff = datetime.now() - timedelta(days=keep_days)
    for p in logs_dir.glob("check_and_retrain_*.log"):
        try:
            if datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
                p.unlink()
        except Exception:
            # best-effort; ignore failures
            pass


def get_label_count(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM labeled_activities")
        row = cur.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        conn.close()


def get_last_manifest_num_labels(models_dir: Path) -> int:
    # Find latest manifest_*.joblib in models/
    manifests = sorted(models_dir.glob("manifest_*.joblib"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not manifests:
        return 0
    try:
        manifest = joblib.load(manifests[0])
        return int(manifest.get("num_labels", 0))
    except Exception:
        return 0


def run_command(python_exe: str, script: str, log_fh) -> int:
    cmd = [python_exe, str(ROOT / script)]
    log_fh.write(f"\n--- Running: {' '.join(cmd)} ---\n")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        log_fh.write(proc.stdout or "")
        if proc.stderr:
            log_fh.write("\n[stderr]\n")
            log_fh.write(proc.stderr)
        log_fh.flush()
        return proc.returncode
    except Exception as ex:
        log_fh.write(f"Exception while running {' '.join(cmd)}: {ex}\n")
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-total", type=int, default=20, help="Minimum total labeled rows required to retrain")
    parser.add_argument("--min-new", type=int, default=10, help="Minimum new labeled rows since last retrain to trigger retrain")
    parser.add_argument("--force", action="store_true", help="Force retrain regardless of thresholds")
    args = parser.parse_args(argv)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOGS_DIR / f"check_and_retrain_{ts}.log"
    python_exe = sys.executable

    # Prune old logs before running
    try:
        prune_old_logs(LOGS_DIR, keep_days=30)
    except Exception:
        pass

    with open(log_path, "a", encoding="utf-8") as log_fh:
        log_fh.write(f"Check-and-Retrain started at {ts}\n")
        log_fh.write(f"Using python: {python_exe}\n")

        current = get_label_count(DB_PATH)
        last = get_last_manifest_num_labels(MODELS_DIR)
        new_labels = current - last

        log_fh.write(f"Current labeled rows: {current}\n")
        log_fh.write(f"Last retrain labeled rows: {last}\n")
        log_fh.write(f"New labels since last retrain: {new_labels}\n")

        should_run = args.force
        if not should_run:
            if current < args.min_total:
                log_fh.write(f"Not enough total labels (need {args.min_total}). Skipping retrain.\n")
            elif new_labels < args.min_new:
                log_fh.write(f"Not enough new labels since last retrain (need {args.min_new}). Skipping retrain.\n")
            else:
                should_run = True

        if should_run:
            log_fh.write("Conditions met — running export, retrain, and archive.\n")
            rc = run_command(python_exe, "export_dataset.py", log_fh)
            if rc != 0:
                log_fh.write(f"export_dataset.py exited with {rc}. Aborting retrain flow.\n")
                print(f"Export failed (rc={rc}). See log: {log_path}")
                return rc

            rc = run_command(python_exe, "retrain_and_version.py", log_fh)
            if rc != 0:
                log_fh.write(f"retrain_and_version.py exited with {rc}. Aborting archive.\n")
                print(f"Retrain failed (rc={rc}). See log: {log_path}")
                return rc

            rc = run_command(python_exe, "archive_dataset.py", log_fh)
            if rc != 0:
                log_fh.write(f"archive_dataset.py exited with {rc}.\n")

            log_fh.write("Retrain flow completed.\n")
            print(f"Retrain executed. See log: {log_path}")
            return 0
        else:
            log_fh.write("Conditions not met — skipping retrain.\n")
            print(f"Retrain skipped. See log: {log_path}")
            return 0


if __name__ == '__main__':
    raise SystemExit(main())
