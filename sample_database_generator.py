import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_NAME = "productivity_agent.db"

# A list of sample activities: (app_name, window_title_keyword, category, avg_duration_min)
SAMPLE_ACTIVITIES = [
    ("Code.exe", "AI Agent Project - main.py", "Productive", 30),
    ("chrome.exe", "Stack Overflow - Python SQLite", "Productive", 10),
    ("chrome.exe", "Google Docs - Project Outline", "Productive", 15),
    ("powershell.exe", "Windows PowerShell", "Productive", 5),
    ("chrome.exe", "YouTube", "Distracting", 20),
    ("chrome.exe", "Reddit - r/machinelearning", "Distracting", 12),
    ("Spotify.exe", "Spotify Premium", "Neutral", 25),
    ("explorer.exe", "File Explorer", "Neutral", 3),
    ("slack.exe", "Slack | #project-ai-agent", "Productive", 5),
    ("winword.exe", "Project Report.docx", "Productive", 18),
]

def create_sample_database():
    """
    Deletes the old database (if it exists) and creates a new one
    populated with realistic sample data from the last 7 days.
    """
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Removed existing database: {DB_NAME}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create tables (copied from database_setup.py for standalone use)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        app_name TEXT NOT NULL,
        window_title TEXT NOT NULL,
        duration_seconds INTEGER NOT NULL,
        category TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labeled_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_text TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL
    )
    """)
    print("Database tables created.")

    # Populate labeled_activities and activity_log
    print("Generating sample data for the last 7 days...")
    for app, title_keyword, category, avg_duration in SAMPLE_ACTIVITIES:
        activity_text = f"{app} | {title_keyword}"
        
        # 1. Add to labeled_activities table to pre-label the data
        try:
            cursor.execute(
                "INSERT INTO labeled_activities (activity_text, category) VALUES (?, ?)",
                (activity_text, category)
            )
        except sqlite3.IntegrityError:
            # This can happen if two sample activities have the same app/title combo
            pass

        # 2. Generate random log entries for the past week
        for day in range(7):
            # Use this activity between 0 and 5 times on a given day
            num_entries = random.randint(0, 5)
            for _ in range(num_entries):
                # Create a random timestamp within that day's 9-to-5 "work" hours
                log_time = datetime.now() - timedelta(days=day, hours=random.randint(-4, 4), minutes=random.randint(0, 59))
                # Create a random duration in seconds, centered around the average
                duration_variance = avg_duration * 0.5
                duration = int(max(60, (avg_duration * 60) + random.randint(-int(duration_variance*60), int(duration_variance*60))))

                cursor.execute(
                    "INSERT INTO activity_log (timestamp, app_name, window_title, duration_seconds) VALUES (?, ?, ?, ?)",
                    (log_time.strftime("%Y-%m-%d %H:%M:%S"), app, title_keyword, duration)
                )

    conn.commit()
    conn.close()
    print(f"\nSample database '{DB_NAME}' created successfully!")
    print("You can now skip data collection/labeling and run:")
    print("1. python train_classifier.py")
    print("2. python run_agent.py")


if __name__ == "__main__":
    create_sample_database()
