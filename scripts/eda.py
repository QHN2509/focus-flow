"""Simple EDA script for labeled activities.

Writes summary JSON and a CSV sample into the `artifacts/` directory.
"""
import os
import sqlite3
import json
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT, "productivity_agent.db")
OUT_DIR = os.path.join(ROOT, "artifacts")


def load_labeled(db_path=DB_PATH):
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Create or copy a DB to run EDA.")
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM labeled_activities", conn)
    finally:
        conn.close()
    return df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_labeled()
    if df.empty:
        print("No labeled data found. Run manual_labeler.py to create labels or generate sample DB.")
        return

    total = len(df)
    if 'category' in df.columns:
        class_counts = df['category'].value_counts().to_dict()
    else:
        class_counts = {}

    summary = {
        "total_samples": int(total),
        "class_distribution": class_counts
    }

    # Save a sample CSV and summary JSON
    sample_csv = os.path.join(OUT_DIR, "sample_labeled_activities.csv")
    df.head(200).to_csv(sample_csv, index=False)

    summary_path = os.path.join(OUT_DIR, "eda_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"EDA complete. Wrote sample: {sample_csv}")
    print(f"Summary written to: {summary_path}")


if __name__ == '__main__':
    main()
