param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('pause','resume')]
    [string]$action
)

$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$pauseFile = Join-Path $project 'pause_collection'

if ($action -eq 'pause') {
    if (-Not (Test-Path $pauseFile)) {
        New-Item -Path $pauseFile -ItemType File | Out-Null
        Write-Host "Created pause file. Data collection will pause."
    } else {
        Write-Host "Pause file already exists."
    }
} else {
    if (Test-Path $pauseFile) {
        Remove-Item $pauseFile
        Write-Host "Removed pause file. Data collection will resume."
    } else {
        Write-Host "Pause file not present."
    }
}
