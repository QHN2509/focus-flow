# Recreate WeeklyRetrain with StartWhenAvailable enabled
$action = New-ScheduledTaskAction -Execute 'C:\Windows\System32\cmd.exe' -Argument '/c "C:\Users\Admin\OneDrive\Documents\Personal_Projects\tools\run_retrain_with_export.cmd"'
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 03:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName 'WeeklyRetrain' -Action $action -Trigger $trigger -Settings $settings -Force

# Print settings to confirm
$s = Get-ScheduledTask -TaskName 'WeeklyRetrain'
$s.Settings | Format-List *

# Also print the task XML for explicit confirmation
Write-Host "--- TASK XML ---"
schtasks /Query /TN WeeklyRetrain /XML
