@echo off
rem Run the daily report from the project root using the project's venv if present
pushd "%~dp0\.."
if exist ".venv\Scripts\python.exe" (
	.venv\Scripts\python.exe run_agent.py %*
) else (
	python run_agent.py %*
)
popd