import shutil
from pathlib import Path
import datetime
import sqlite3
import os

EXPORT_DIR = Path('dataset_exports')
ARCHIVE_DIR = Path('archives')
ARCHIVE_DIR.mkdir(exist_ok=True)

def export_and_archive():
    # Run export (uses export_dataset.py's output path)
    os.system(f"{os.environ.get('PYTHON','python')} export_dataset.py")
    if not EXPORT_DIR.exists():
        print("No exports found to archive.")
        return

    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    archive_name = ARCHIVE_DIR / f'dataset-{ts}.zip'
    shutil.make_archive(str(archive_name).replace('.zip',''), 'zip', EXPORT_DIR)
    print(f"Created archive: {archive_name}")

def prune_older_than(days=365):
    """Optional: prune activity_log rows older than `days`. Disabled by default."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    conn = sqlite3.connect('productivity_agent.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activity_log WHERE timestamp < ?", (cutoff.strftime('%Y-%m-%d %H:%M:%S'),))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"Pruned {deleted} rows older than {days} days")

if __name__ == '__main__':
    export_and_archive()
