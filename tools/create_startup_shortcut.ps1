<#
Create a shortcut in the current user's Startup folder that runs the collector wrapper.
Usage: Run this in PowerShell (no admin required):
    .\tools\create_startup_shortcut.ps1
#>
param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$ShortcutName = "FocusFlowCollector.lnk"
)

$startup = [Environment]::GetFolderPath('Startup')
$target = Join-Path -Path $RepoPath -ChildPath "tools\run_collector.cmd"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut((Join-Path $startup $ShortcutName))
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $RepoPath
$shortcut.WindowStyle = 1
$shortcut.Save()
Write-Output "Shortcut created: $(Join-Path $startup $ShortcutName) -> $target"
