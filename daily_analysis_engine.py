import sqlite3
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta

DB_NAME = "productivity_agent.db"
MODEL_PATH = "classifier_model.joblib"

def classify_new_activities():
    """Classifies all unlabeled activities in the log using the trained model."""
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Please train the model first using train_classifier.py.")
        return
    
    model = joblib.load(MODEL_PATH)
    conn = sqlite3.connect(DB_NAME)
    
    # Get unlabeled activities
    df = pd.read_sql_query("SELECT id, app_name, window_title FROM activity_log WHERE category IS NULL", conn)
    
    if df.empty:
        print("No new activities to classify.")
        conn.close()
        return

    df['activity_text'] = df['app_name'] + ' | ' + df['window_title']
    
    # Predict categories
    predictions = model.predict(df['activity_text'])
    df['category'] = predictions
    
    # Update database
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("UPDATE activity_log SET category = ? WHERE id = ?", (row['category'], row['id']))
    
    conn.commit()
    conn.close()
    print(f"Successfully classified {len(df)} new activities.")


def generate_daily_report():
    """
    Generates a full productivity report for the previous day, including
    summary, anomalies, forecast, and recommendations.
    """
    conn = sqlite3.connect(DB_NAME)
    
    # --- 1. Get Yesterday's Data ---
    yesterday = datetime.now().date() - timedelta(days=1)
    start_of_day = datetime.combine(yesterday, datetime.min.time())
    end_of_day = datetime.combine(yesterday, datetime.max.time())
    
    query = f"SELECT * FROM activity_log WHERE timestamp BETWEEN '{start_of_day}' AND '{end_of_day}'"
    df_today = pd.read_sql_query(query, conn)

    if df_today.empty:
        return f"Productivity Report for {yesterday.strftime('%A, %B %d')}\n\nNo activity logged yesterday.", ""

    # --- 2. Calculate Yesterday's Summary ---
    # total seconds per category
    summary_seconds = df_today.groupby('category')['duration_seconds'].sum()

    def _format_seconds(sec: int) -> str:
        """Format seconds as 'Xh Ym' or 'Ym' if less than 1 hour."""
        try:
            sec = int(sec)
        except Exception:
            return "0m"
        hours = sec // 3600
        minutes = (sec % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    summary_text = (
        f"Productivity Report for {yesterday.strftime('%A, %B %d')}\n"
        f"Data window: {start_of_day.strftime('%Y-%m-%d %H:%M:%S')} — {end_of_day.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "--- Yesterday's Summary ---\n"
    )
    for category, seconds in summary_seconds.items():
        summary_text += f"- {category}: {_format_seconds(seconds)}\n"
        
    # --- 3. Get Historical Data for Comparison ---
    thirty_days_ago = datetime.now() - timedelta(days=30)
    query_hist = f"SELECT timestamp, category, duration_seconds FROM activity_log WHERE timestamp >= '{thirty_days_ago}'"
    df_hist = pd.read_sql_query(query_hist, conn, parse_dates=['timestamp'])
    df_hist['date'] = df_hist['timestamp'].dt.date
    
    # Daily summary for the last 30 days
    daily_summary_hist = (df_hist.groupby(['date', 'category'])['duration_seconds'].sum() / 3600).unstack(fill_value=0)
    
    report_sections = [summary_text]
    
    # --- 4. Anomaly Detection ---
    anomaly_text = "\n--- Anomaly Detection ---\n"
    has_anomaly = False
    # use hours for statistical comparison, but display formatted time
    daily_summary_hours = (daily_summary_hist / 3600) if not daily_summary_hist.empty else daily_summary_hist
    for category in summary_seconds.index:
        if category in daily_summary_hours.columns:
            mean = daily_summary_hours[category].mean()
            std = daily_summary_hours[category].std()
            today_hours = (summary_seconds.get(category, 0) / 3600)
            if std is None:
                std = 0
            if today_hours > (mean + 2 * std):
                anomaly_text += (
                    f"! High Usage Alert: You spent {_format_seconds(summary_seconds.get(category,0))} on '{category}', "
                    f"significantly more than your 30-day average of {mean:.2f} hours.\n"
                )
                has_anomaly = True
    if not has_anomaly:
        anomaly_text += "Your usage patterns were normal yesterday. Great consistency!\n"
    report_sections.append(anomaly_text)
    
    # --- 5. Forecast (7-day moving average) ---
    forecast_text = "\n--- Forecast for Today ---\n"
    seven_days_ago = datetime.now().date() - timedelta(days=7)
    df_week = daily_summary_hist[daily_summary_hist.index >= seven_days_ago]

    forecast_hours = df_week.mean() if not df_week.empty else pd.Series()
    for category, hours in forecast_hours.items():
        seconds = int(hours * 3600)
        forecast_text += f"- You're likely to spend ~{_format_seconds(seconds)} on '{category}'.\n"
    report_sections.append(forecast_text)
        
    # --- 6. Recommendations (Rule-based) ---
    rec_text = "\n--- Recommendations ---\n"
    distracting_avg = forecast_hours.get('Distracting', 0)
    distracting_today = (summary_seconds.get('Distracting', 0) / 3600)

    if distracting_today > distracting_avg * 1.2 and distracting_avg > 0:
        rec_text += (
            f"- Distracting activities were high yesterday. Try to keep it under {distracting_avg:.1f} hours today.\n"
        )
    else:
        rec_text += "- You're managing distractions well. Keep it up!\n"

    productive_avg = forecast_hours.get('Productive', 0)
    productive_today = (summary_seconds.get('Productive', 0) / 3600)

    if productive_avg > 0 and productive_today < productive_avg * 0.8:
        rec_text += (
            f"- Productive time was lower than usual. Try scheduling a 1-hour focus block to get back on track.\n"
        )
    report_sections.append(rec_text)

    # Create a short summary for notifications (hours+minutes)
    def _fmt_cat(cat):
        return _format_seconds(summary_seconds.get(cat, 0))

    notification_summary = f"Distracting: {_fmt_cat('Distracting')}, Productive: {_fmt_cat('Productive')}"

    # Add a short note about task scheduling/time frames
    schedule_note = (
        "\n--- Task timeframes ---\n"
        "Collector: designed to run continuously (trigger: ONLOGON). "
        "Report: scheduled daily (time configurable using tools/create_tasks.ps1).\n"
    )
    report_sections.append(schedule_note)

    conn.close()
    return "".join(report_sections), notification_summary


if __name__ == '__main__':
    # For testing purposes
    classify_new_activities()
    full_report, _ = generate_daily_report()
    print(full_report)
