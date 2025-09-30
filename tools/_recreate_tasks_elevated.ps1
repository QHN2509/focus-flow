$collectorTaskName = 'FocusFlowCollector'
$reportTaskName = 'FocusFlowDailyReport'
$collectorCmd = 'C:\Users\Admin\OneDrive\Documents\Personal_Projects\tools\run_collector.cmd'
$reportCmd = 'C:\Users\Admin\OneDrive\Documents\Personal_Projects\tools\run_report.cmd'
$reportTime = '08:00'

Write-Host "Deleting existing tasks (if present)..."
try { schtasks /Delete /TN $collectorTaskName /F } catch {}
try { schtasks /Delete /TN $reportTaskName /F } catch {}

Write-Host "Creating tasks pointing to cmd.exe with wrapper scripts as arguments..."
$collectorTR = 'cmd.exe /c "' + $collectorCmd + '"'
$reportTR = 'cmd.exe /c "' + $reportCmd + '"'

schtasks /Create /SC ONLOGON /TN $collectorTaskName /TR $collectorTR /RL HIGHEST /F
schtasks /Create /SC DAILY /TN $reportTaskName /TR $reportTR /ST $reportTime /RL HIGHEST /F

Write-Host "Done."