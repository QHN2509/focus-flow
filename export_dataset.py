import sqlite3
import pandas as pd
from pathlib import Path

DB_NAME = "productivity_agent.db"
OUT_DIR = Path("dataset_exports")

def export_all():
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    try:
        df_log = pd.read_sql_query("SELECT * FROM activity_log", conn)
        df_labels = pd.read_sql_query("SELECT * FROM labeled_activities", conn)
        df_log.to_csv(OUT_DIR / "activity_log_full.csv", index=False)
        df_labels.to_csv(OUT_DIR / "labeled_activities_full.csv", index=False)
        print(f"Exported activity_log_full.csv and labeled_activities_full.csv to {OUT_DIR}")
    finally:
        conn.close()

if __name__ == '__main__':
    export_all()
