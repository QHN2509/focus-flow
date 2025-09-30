import daily_analysis_engine as daily_analysis
from plyer import notification
import time

def main():
    """
    Main function to run the daily agent tasks and display the report.
    """
    print("Running FocusFlow...")
    
    # Step 1: Classify any new data that has been collected
    print("\n[1/3] Classifying new activities...")
    daily_analysis.classify_new_activities()
    time.sleep(1)

    # Step 2: Generate the comprehensive daily report
    print("[2/3] Generating daily report...")
    full_report, notification_summary = daily_analysis.generate_daily_report()
    time.sleep(1)

    # Step 3: Display the report and send a notification
    print("\n[3/3] Report generated!")
    print("-" * 50)
    print(full_report)
    print("-" * 50)

    try:
        notification.notify(
            title='Your Daily Productivity Report is Ready!',
            message=notification_summary,
            app_name='FocusFlow',
            timeout=20  # Notification will disappear after 20 seconds
        )
        print("Desktop notification sent.")
    except Exception as e:
        print(f"Could not send desktop notification: {e}")
        print("Please ensure you have a notification backend installed (e.g., on Linux).")


if __name__ == "__main__":
    main()
