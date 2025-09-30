## FocusFlow — AI personal productivity assistant

FocusFlow is a local-first assistant that tracks active windows, learns which activities you consider "productive", and generates daily productivity reports with simple recommendations. All data is stored locally in a SQLite database.

## What this project contains

- `data_collector.py` — tracks the active window and logs to `productivity_agent.db`.
- `manual_labeler.py` — interactive labeling tool for activities.
- `train_classifier.py` — trains a TF‑IDF + LogisticRegression model and saves `classifier_model.joblib`.
- `run_agent.py` — classifies new activities and generates a daily report.
- `export_dataset.py`, `retrain_and_version.py`, `archive_dataset.py` — helpers for export, versioning and archiving.
- `tools/` — helpers for scheduling and toggling collection (see below).

## Quick start (Windows / macOS / Linux)

These instructions aim to make the project portable so it can be published to GitHub and used on other machines.

1. Install Python 3.8+ and create a virtual environment (recommended):

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux (bash/zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Initialize the SQLite database:

```bash
python database_setup.py
```

3. (Optional) Generate a sample database to test quickly (this may overwrite an existing DB):

```bash
python sample_database_generator.py
```

## How to use

1. Collect data

Run the collector and leave it running while you use your computer. Prefer the wrapper in `tools/` which sets the project working directory and uses the local venv when present.

Windows (run the Batch wrapper):

```powershell
.\tools\run_collector.cmd
```

macOS / Linux (run the shell wrapper):

```bash
./tools/run_collector.sh
```

Or run directly (if not using wrappers):

```bash
python data_collector.py
```

Press Ctrl+C to stop. The collector writes activity records to `productivity_agent.db`.

2. Label activities

Teach the agent which activities are productive:

```bash
python manual_labeler.py
```

Use `p` (productive), `d` (distracting), `n` (neutral) or `s` (skip).

3. Train the model

After labeling enough activities (recommended >= 20; more is better):

```bash
python train_classifier.py
```

This writes `classifier_model.joblib`. You can use `retrain_and_version.py` to produce timestamped model builds. Use the `tools/` wrappers to schedule retraining; the retrain wrapper will only run when there are enough new labels (see `tools/check_and_retrain.py`).

4. Run the daily report

Use the wrapper in `tools/` to ensure the proper working directory and venv are used.

Windows:

```powershell
.\tools\run_report.cmd
```

macOS / Linux:

```bash
./tools/run_report.sh
```

Or run directly:

```bash
python run_agent.py
```

This will classify any unclassified activities and print/send a daily report.

## Scheduling (Windows Task Scheduler)

Helpers live in `tools/`:

- `tools/create_tasks.ps1` — writes wrapper CMDs and registers two tasks:
	- `FocusFlowCollector` — ONLOGON (collector)
	- `FocusFlowDailyReport` — DAILY (report)
- `tools/remove_tasks.ps1` — delete the scheduled tasks (interactive / supports `-Force`).

Notes:
- Creating tasks with highest privileges typically requires running `create_tasks.ps1` as Administrator. If you see "Access is denied", re-run the script in an elevated PowerShell (right-click → Run as Administrator).
- The wrapper files in `tools/` are portable and intentionally avoid absolute paths; they prefer the project's `.venv` when present and fall back to the system Python.
- For non-Windows systems you can use a cron job, launchd (macOS), or a systemd timer to call the shell wrappers in `tools/`.

## Toggle collection quickly

A `pause_collection` file in the project root pauses the collector. Use the toggle helper:

```powershell
.\tools\toggle_collection.ps1
```

## Where outputs go

- Database: `productivity_agent.db`
- Exports: `dataset_exports/`
- Models: `models/` (timestamped) and `classifier_model.joblib`
- Archives: `archives/`

## Artifacts, metrics and a resume snippet

After training, the project writes evaluation artifacts and timestamped models to the `artifacts/` folder. Useful files you can include in a GitHub release or reference on your resume:

- `artifacts/model_<TIMESTAMP>.joblib` — trained pipeline (TF‑IDF + LogisticRegression).
- `classifier_model.joblib` — legacy model filename (kept for backwards compatibility).
- `artifacts/classification_report.txt` — human-readable classification report (precision/recall/F1).
- `artifacts/classification_report.json` — machine-readable report useful for badges or programmatic checks.
- `artifacts/confusion_matrix.png` — PNG of the confusion matrix for a visual in your README or portfolio.
- `artifacts/cv_summary.json` — cross-validation summary (mean/std for accuracy, precision, recall, F1).
- `artifacts/metadata_<TIMESTAMP>.json` — training metadata (timestamp, sample counts, class distribution, artifact paths).

Tip: run `python train_classifier.py` after you have at least ~20 labeled samples; then copy the most recent `metadata_*.json` values into the resume snippet below so your portfolio has concrete numbers.

Suggested resume bullets (pick one or both). These examples are filled with values from the most recent training run in `artifacts/metadata_20250930T032631Z.json` — update them after retraining if you improve the model:

- "Built FocusFlow, a local activity-logging and classification pipeline (Python, SQLite, scikit-learn). Collected and labeled 50 activity examples and trained a TF‑IDF + LogisticRegression model; achieved macro-F1 0.15 on a held-out test set. Automations include scheduled data collection and model retraining with timestamped artifacts (`artifacts/classifier_model_20250930T032631Z.joblib`)."

- "Implemented end-to-end ML lifecycle for a privacy-first productivity assistant: data collection, manual labeling, cross‑validated training, and automated daily reporting. Produced reproducible artifacts (confusion matrix, classification report and CV summary) and versioned models for auditability."

If you'd like, I can re-run training and insert the latest `confusion_matrix.png` inline in the README and update these numbers automatically after each retrain.
Below is the latest confusion matrix generated during the most recent training run (see `artifacts/confusion_matrix.png`).

![Confusion matrix](artifacts/confusion_matrix.png)

## Troubleshooting

- Training errors mentioning `numpy.dtype size changed` or binary incompatibility: create a fresh virtualenv and reinstall dependencies from `requirements.txt`.
- If scheduled tasks run but return a non-zero Last Result, inspect the task's XML with `schtasks /Query /TN <TaskName> /XML` and run the wrapper CMD manually to see output.
- If the collector doesn't log anything:
	- Verify required platform package is installed (Windows: `pywin32`).
	- Ensure `pause_collection` file doesn't exist.
	- Check `EXCLUDE_APPS` in `data_collector.py`.

## Privacy

All activity and labels are stored locally in `productivity_agent.db`. The project does not transmit personal data externally by default.

## Publishing to GitHub

To prepare this repository for public use:

1. Ensure `requirements.txt` lists all dependencies.
2. Remove any personal secrets or local absolute paths.
3. Add a license (e.g., MIT) as `LICENSE` if you want others to use/modify the code.
4. Commit and push to a new GitHub repository. The project uses only standard Python packages and local files; no secrets are included.

I can also:
- Add `tools/README.md` describing task creation/removal and a no-elevation Startup-folder fallback.
- Add a GitHub Actions workflow to run linting and unit tests on push.

If you'd like me to add any of these, tell me which and I'll implement them.

Additional quick helpers included

- Startup shortcut helper: `tools/create_startup_shortcut.ps1` — run this in PowerShell (no admin required) to place a shortcut in your user Startup folder that runs `tools/run_collector.cmd` at logon.

- Smoke test: `tools/smoke_test.py` — a small script that verifies required imports. CI runs this automatically; you can run it locally with:

```bash
# Windows (PowerShell)
.venv\Scripts\python.exe tools\smoke_test.py

# macOS / Linux
.venv/bin/python tools/smoke_test.py
```

- Pinned requirements: I can generate a pinned requirements file from your current venv for reproducible installs. A generated file named `requirements-pinned.txt` is useful for releasing a tagged version. If you'd like, I can add that file to the repo now.