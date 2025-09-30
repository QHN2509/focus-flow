@echo off
rem Run conditional retrain from project root using venv if present
pushd "%~dp0\.."
if exist ".venv\Scripts\python.exe" (
	.venv\Scripts\python.exe tools\check_and_retrain.py --min-new 5 %*
) else (
	python tools\check_and_retrain.py --min-new 5 %*
)
popd