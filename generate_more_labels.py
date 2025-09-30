import sqlite3
import os

DB_NAME = "productivity_agent.db"
TARGET_LABELS = 50

def ensure_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labeled_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_text TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL
    )
    """)
    conn.commit()

def generate_labels():
    created = 0
    conn = sqlite3.connect(DB_NAME)
    ensure_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM labeled_activities")
    row = cursor.fetchone()
    current = row[0] if row else 0
    print(f"Current labeled activities: {current}")

    categories = ["Productive", "Distracting", "Neutral"]
    i = 0
    # Start index for synthetic labels so we don't collide with existing ones
    start_index = current + 1
    while current < TARGET_LABELS:
        activity_text = f"auto_app_{start_index + i}.exe | Auto Activity {start_index + i}"
        category = categories[(start_index + i) % len(categories)]
        try:
            cursor.execute(
                "INSERT INTO labeled_activities (activity_text, category) VALUES (?, ?)",
                (activity_text, category)
            )
            conn.commit()
            created += 1
            current += 1
        except sqlite3.IntegrityError:
            # If the synthetic key somehow exists, skip
            pass
        i += 1

    conn.close()
    print(f"Inserted {created} synthetic labeled activities. New total: {current}")

if __name__ == '__main__':
    # Ensure database file exists (the script will create it if needed)
    if not os.path.exists(DB_NAME):
        # Touch the file by connecting
        conn = sqlite3.connect(DB_NAME)
        conn.close()
        print(f"Created new database file: {DB_NAME}")

    generate_labels()
