param(
    [string]$collectorTaskName = 'FocusFlowCollector',
    [string]$reportTaskName = 'FocusFlowDailyReport',
    [string]$pythonExe = '',
    [string]$projectPath = '',
    [string]$reportTime = '08:00'
)

# Resolve defaults
if ([string]::IsNullOrEmpty($projectPath)) { $projectPath = (Get-Location).Path }
if ([string]::IsNullOrEmpty($pythonExe)) { $pythonExe = Join-Path $projectPath '.venv\Scripts\python.exe' }

$toolsDir = Join-Path $projectPath 'tools'
if (-not (Test-Path $toolsDir)) { New-Item -ItemType Directory -Path $toolsDir | Out-Null }

$collectorCmd = Join-Path $toolsDir 'run_collector.cmd'
$reportCmd = Join-Path $toolsDir 'run_report.cmd'

Write-Host "Writing wrapper CMD files to: $toolsDir"

$collectorContent = @"
@echo off
cd /d "$projectPath"
"$pythonExe" "$projectPath\data_collector.py"
"@

$reportContent = @"
@echo off
cd /d "$projectPath"
"$pythonExe" "$projectPath\run_agent.py"
"@

[System.IO.File]::WriteAllText($collectorCmd, $collectorContent)
[System.IO.File]::WriteAllText($reportCmd, $reportContent)

Write-Host "Wrapper CMD files written: `n - $collectorCmd `n - $reportCmd"

function Create-Task($name, $cmdPath, $scheduleArgs) {
    $tr = '"' + $cmdPath + '"'
    $baseArgs = @('/Create') + $scheduleArgs + @('/TN', $name, '/TR', $tr)

    # First try: register with highest privileges (may require elevation)
    $argsWithRL = $baseArgs + @('/RL', 'HIGHEST', '/F')
    Write-Host "Registering scheduled task: $name (attempt with /RL HIGHEST)"
    Write-Host "schtasks " + ($argsWithRL -join ' ')
    $proc = Start-Process -FilePath schtasks -ArgumentList $argsWithRL -NoNewWindow -Wait -PassThru

    if ($proc.ExitCode -eq 0) {
        Write-Host "Scheduled task '$name' created successfully (with HIGHEST)."
        return
    }

    Write-Warning "schtasks returned exit code $($proc.ExitCode) when trying with /RL HIGHEST. Retrying without /RL to create a user-level task..."

    # Retry without RL; this often works for non-elevated users (creates a task under current user)
    $argsNoRL = $baseArgs + @('/F')
    Write-Host "schtasks " + ($argsNoRL -join ' ')
    $proc2 = Start-Process -FilePath schtasks -ArgumentList $argsNoRL -NoNewWindow -Wait -PassThru
    if ($proc2.ExitCode -ne 0) {
        Write-Warning "schtasks retry returned exit code $($proc2.ExitCode). You may need to run this script as Administrator to register tasks with highest privileges."
    } else {
        Write-Host "Scheduled task '$name' created successfully (without RL)."
    }
}

try {
    Create-Task -name $collectorTaskName -cmdPath $collectorCmd -scheduleArgs @('/SC','ONLOGON')
} catch {
    Write-Warning "Failed to create collector task: $_"
}

try {
    Create-Task -name $reportTaskName -cmdPath $reportCmd -scheduleArgs @('/SC','DAILY','/ST',$reportTime)
} catch {
    Write-Warning "Failed to create report task: $_"
}

Write-Host "Done. If task creation failed with 'Access is denied', re-run this script in an elevated PowerShell (Run as Administrator)."
