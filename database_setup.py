import sqlite3

DB_NAME = "productivity_agent.db"

def setup_database():
    """Initializes the SQLite database and creates the necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Main log of all activities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        app_name TEXT NOT NULL,
        window_title TEXT NOT NULL,
        duration_seconds INTEGER NOT NULL,
        category TEXT
    )
    """)

    # Table to store user-defined labels for unique activities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labeled_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_text TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL
    )
    """)
    
    print(f"Database '{DB_NAME}' checked and tables are ready.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
