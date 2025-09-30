import sqlite3
import pandas as pd

DB_NAME = "productivity_agent.db"

def get_unlabeled_activities():
    """
    Retrieves unique activities from the log that haven't been labeled yet.
    Returns:
        (list): A list of unique activity strings to be labeled.
    """
    conn = sqlite3.connect(DB_NAME)
    
    # Get all unique app/title combinations from the log
    log_df = pd.read_sql_query("SELECT DISTINCT app_name, window_title FROM activity_log", conn)
    log_df["activity_text"] = log_df["app_name"] + " | " + log_df["window_title"]
    
    # Get all activities that are already labeled
    labeled_df = pd.read_sql_query("SELECT activity_text FROM labeled_activities", conn)
    
    # Find the activities that are not yet in the labeled table
    unlabeled = log_df[~log_df["activity_text"].isin(labeled_df["activity_text"])]
    
    conn.close()
    
    return list(unlabeled["activity_text"].unique())

def save_label(activity_text, category):
    """Saves a new label to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO labeled_activities (activity_text, category) VALUES (?, ?)",
            (activity_text, category)
        )
        conn.commit()
        print(f"Saved: '{category}'")
    except sqlite3.IntegrityError:
        print("Label for this activity already exists.")
    finally:
        conn.close()

def main():
    """Main loop for the manual labeling process."""
    print("--- Manual Activity Labeler ---")
    print("Classify each activity as (p)roductive, (d)istracting, (n)eutral, or (s)kip.")
    
    unlabeled_activities = get_unlabeled_activities()
    
    if not unlabeled_activities:
        print("\nNo new activities to label. Collect more data first!")
        return

    for activity in unlabeled_activities:
        while True:
            # Shorten long window titles for display
            display_activity = activity
            if len(display_activity) > 150:
                display_activity = display_activity[:147] + "..."

            label = input(f"\nActivity: {display_activity}\nClassify as [p/d/n/s]: ").lower()
            
            if label == 'p':
                save_label(activity, "Productive")
                break
            elif label == 'd':
                save_label(activity, "Distracting")
                break
            elif label == 'n':
                save_label(activity, "Neutral")
                break
            elif label == 's':
                print("Skipped.")
                break
            else:
                print("Invalid input. Please enter 'p', 'd', 'n', or 's'.")

    print("\n--- Labeling complete! ---")

if __name__ == "__main__":
    main()
