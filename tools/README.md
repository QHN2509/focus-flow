# tools/ — scheduling helpers

This folder contains helpers to create/remove scheduled tasks (Windows) and simple wrappers that make running scripts reliable across platforms.

Files of interest

- `run_collector.cmd` / `run_collector.sh` — wrapper to start the collector from the project root and use the local `.venv` when present.
- `run_report.cmd` / `run_report.sh` — wrapper to run the daily report.
- `run_retrain.cmd` / `run_retrain_with_export.cmd` — wrappers that call `tools/check_and_retrain.py` which conditionally runs export/retrain/archive.
- `check_and_retrain.py` — checks labeled counts and only triggers the retrain flow when thresholds are met. Writes logs to `tools/logs/` and prunes logs older than 30 days.
- `create_tasks.ps1` / `remove_tasks.ps1` — PowerShell scripts that can create or remove Task Scheduler entries. `create_tasks.ps1` creates wrapper CMDs and registers tasks.
- `toggle_collection.ps1` — toggles a `pause_collection` file in the project root to pause/resume collection.

Quick notes

- Task Scheduler: creating tasks with highest privileges requires Administrator. If you see "Access is denied", run the respective script in an elevated PowerShell.
- No-elevation fallback: if you don't want to use Task Scheduler, create a shortcut to `tools/run_collector.cmd` in your Windows Startup folder (shell:startup). On macOS use `launchd` and on Linux use `cron` or `systemd` user timers.

Example: create a Startup shortcut on Windows

1. Press Win+R and run `shell:startup` to open the Startup folder.
2. Right-click → New → Shortcut.
3. Point it to `C:\path\to\repo\tools\run_collector.cmd` and give it a name.

If you want, I can add a PowerShell helper that creates that shortcut programmatically.
