param(
    [string]$taskName = 'WeeklyRetrain',
    [string]$pythonExe = '',
    [string]$projectPath = '',
    [string]$dayOfWeek = 'SUN',    # MON|TUE|WED|THU|FRI|SAT|SUN
    [string]$time = '03:00',       # HH:mm (24h)
    [switch]$ArchiveExport         # if set, run export and archive before retrain
)

if ([string]::IsNullOrEmpty($projectPath)) { $projectPath = (Get-Location).Path }
if ([string]::IsNullOrEmpty($pythonExe)) { $pythonExe = Join-Path $projectPath '.venv\Scripts\python.exe' }

$toolsDir = Join-Path $projectPath 'tools'
if (-not (Test-Path $toolsDir)) { New-Item -ItemType Directory -Path $toolsDir | Out-Null }

$retrainCmd = Join-Path $toolsDir 'run_retrain.cmd'
$retrainWithExportCmd = Join-Path $toolsDir 'run_retrain_with_export.cmd'

Write-Host "Writing wrapper CMD files in: $toolsDir"

$retrainContent = @"
@echo off
cd /d "$projectPath"
"$pythonExe" "$projectPath\retrain_and_version.py"
"@

$retrainWithExportContent = @"
@echo off
cd /d "$projectPath"
"$pythonExe" "$projectPath\export_dataset.py"
"$pythonExe" "$projectPath\retrain_and_version.py"
"$pythonExe" "$projectPath\archive_dataset.py"
"@

[System.IO.File]::WriteAllText($retrainCmd, $retrainContent)
[System.IO.File]::WriteAllText($retrainWithExportCmd, $retrainWithExportContent)

Write-Host "Wrapper CMD files created:\n - $retrainCmd\n - $retrainWithExportCmd"

# Choose which wrapper to schedule
$cmdToUse = $retrainCmd
if ($ArchiveExport.IsPresent) { $cmdToUse = $retrainWithExportCmd }

# Build the schtasks TR argument to run cmd.exe with the wrapper (properly quoted)
# We want the TR to look like: "C:\Windows\System32\cmd.exe" /c "C:\full\path\to\wrapper.cmd"
$cmdExeFull = Join-Path $env:windir 'System32\cmd.exe'
$tr = '"' + $cmdExeFull + '" /c "' + $cmdToUse + '"'

# Create the scheduled task (weekly)
Write-Host "Creating scheduled task '$taskName' weekly on $dayOfWeek at $time (may require elevation)."
$createArgs = @('/Create','/SC','WEEKLY','/D',$dayOfWeek,'/ST',$time,'/TN',$taskName,'/TR',$tr,'/RL','HIGHEST','/F')

& schtasks /Create /SC WEEKLY /D $dayOfWeek /ST $time /TN $taskName /TR $tr /RL HIGHEST /F
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Initial schtasks call returned exit code $LASTEXITCODE. Retrying without /RL (user-level task)..."
    & schtasks /Create /SC WEEKLY /D $dayOfWeek /ST $time /TN $taskName /TR $tr /F
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Retry failed with exit code $LASTEXITCODE. You may need to run this script as Administrator to register the task."
    } else {
        Write-Host "Scheduled task created (user-level)."
    }
} else {
    Write-Host "Scheduled task created with highest privileges."
}

Write-Host "Done."