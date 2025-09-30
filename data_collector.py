import time
import sqlite3
import sys
import psutil
import os

# --- Platform-specific imports for getting active window ---
try:
    if sys.platform == "win32":
        import win32gui
        import win32process
    elif sys.platform == "darwin":  # macOS
        from AppKit import NSWorkspace
    elif sys.platform == "linux":
        from Xlib import display
except ImportError as e:
    print(f"Platform-specific library not found: {e}")
    print("Please install the required library for your OS (pywin32, py-applescript, or python-xlib).")
    sys.exit(1)

DB_NAME = "productivity_agent.db"
# Interval between active-window checks (seconds). Increase to reduce CPU/I/O.
CHECK_INTERVAL_SECONDS = 5  # default to 5 seconds

# Optional pause file: if this file exists in the project folder, the collector
# will pause (useful to quickly stop collection without touching scheduled tasks).
PAUSE_FILE = os.path.join(os.path.dirname(__file__), "pause_collection")

# Exclude logging for specific apps (process names). Example: ['explorer.exe']
EXCLUDE_APPS = []

# If True, pause collection when on battery power (laptops). Requires psutil.
PAUSE_ON_BATTERY = False

def get_active_window_info():
    """
    Gets the application name and window title of the currently active window.
    Returns:
        (tuple): A tuple containing (app_name, window_title) or (None, None) on error.
    """
    try:
        if sys.platform == "win32":
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                process = psutil.Process(pid)
                app_name = process.name()
                window_title = win32gui.GetWindowText(hwnd)
                return app_name, window_title
    except Exception as e:
        print(f"Error retrieving active window info: {e}")
        return None, None
        return None, None

    if sys.platform == "darwin":
        try:
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            app_name = active_app.localizedName()
            # This is more complex on macOS to get window title accurately,
            # so we'll often rely on the app name.
            window_title = "macOS Active Window" # Placeholder
            return app_name, window_title
        except Exception as e:
            print(f"Error retrieving active window info on macOS: {e}")
            return None, None

    elif sys.platform == "linux":
        try:
            d = display.Display()
            root = d.screen().root
            window_id = root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'), 0).value[0]
            window = d.create_resource_object('window', window_id)
            window_title = window.get_wm_name()
            
            pid = window.get_full_property(d.intern_atom('_NET_WM_PID'), 0).value[0]
            process = psutil.Process(pid)
            app_name = process.name()

            return app_name, window_title
        except Exception as e:
            print(f"Error retrieving active window info on Linux: {e}")
            return None, None

    return None, None

def log_activity(app_name, window_title, duration):
    """Logs an activity to the database."""
    if not app_name or duration < 1:
        return
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_log (app_name, window_title, duration_seconds) VALUES (?, ?, ?)",
            (app_name, window_title, duration)
        )
        conn.commit()
        conn.close()
        print(f"Logged: {app_name} - {window_title[:50]}... for {duration}s")
    except sqlite3.Error as e:
        print(f"Database error: {e}")


def main():
    """Main loop to track and log user activity."""
    print("Starting data collector... Press Ctrl+C to stop.")
    
    last_app = None
    last_title = None
    start_time = time.time()
    paused_state = False

    try:
        while True:
            # Pause if a pause file exists
            if os.path.exists(PAUSE_FILE):
                if not paused_state:
                    print("Data collection paused (pause file present).")
                    paused_state = True
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue
            else:
                if paused_state:
                    print("Data collection resumed.")
                    paused_state = False

            # Optional: pause on battery
            try:
                if PAUSE_ON_BATTERY:
                    batt = psutil.sensors_battery()
                    if batt is not None and not batt.power_plugged:
                        # On battery and configured to pause
                        if not paused_state:
                            print("Data collection paused (on battery).")
                            paused_state = True
                        time.sleep(CHECK_INTERVAL_SECONDS)
                        continue
                    else:
                        if paused_state and (batt is None or batt.power_plugged):
                            print("Data collection resumed (on AC power).")
                            paused_state = False
            except Exception:
                # If psutil battery check fails for any reason, ignore and continue
                pass

            app, title = get_active_window_info()

            if app is not None:
                # Respect exclusion list
                if app in EXCLUDE_APPS:
                    # Treat excluded apps as 'no activity' for logging purposes
                    app = None
                    title = None

                if app != last_app or title != last_title:
                    # Window has changed, log the duration of the last activity
                    duration = int(time.time() - start_time)
                    if duration > 0:
                        log_activity(last_app, last_title, duration)
                    
                    # Reset for the new activity
                    last_app = app
                    last_title = title
                    start_time = time.time()
            
            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        # Log the final activity before exiting
        duration = int(time.time() - start_time)
        log_activity(last_app, last_title, duration)
        print("\nData collector stopped.")

if __name__ == "__main__":
    main()
