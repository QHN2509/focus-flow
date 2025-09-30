# Recreate FocusFlowDailyReport with StartWhenAvailable enabled
$action = New-ScheduledTaskAction -Execute 'C:\Windows\System32\cmd.exe' -Argument '/c "C:\Users\Admin\OneDrive\Documents\Personal_Projects\tools\run_report.cmd"'
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
# -StartWhenAvailable is a switch parameter (no explicit value)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

$
Register-ScheduledTask -TaskName 'FocusFlowDailyReport' -Action $action -Trigger $trigger -Settings $settings -Force

# Print settings to confirm
 $s = Get-ScheduledTask -TaskName 'FocusFlowDailyReport'
$s.Settings | Format-List *

# Also print the task XML for explicit confirmation
Write-Host "--- TASK XML ---"
schtasks /Query /TN FocusFlowDailyReport /XML
