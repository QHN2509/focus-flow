@echo off
rem Run the collector from the project root using the project's venv if present
pushd "%~dp0\.."
if exist ".venv\Scripts\python.exe" (
	.venv\Scripts\python.exe data_collector.py %*
) else (
	python data_collector.py %*
)
popd