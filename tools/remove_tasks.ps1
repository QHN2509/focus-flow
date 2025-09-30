param(
    [string]$collectorTaskName = 'FocusFlowCollector',
    [string]$reportTaskName = 'FocusFlowDailyReport',
    [switch]$Force
)

function Confirm-And-Delete($taskName) {
    if (-not $Force) {
        try {
            schtasks /Query /TN $taskName | Out-Null
        } catch {
            Write-Host "Task '$taskName' not found. Skipping."
            return
        }

        $answer = Read-Host "Delete scheduled task '$taskName'? (Y/N)"
        if ($answer -notin @('Y','y')) {
            Write-Host "Skipping deletion of '$taskName'."
            return
        }
    }

    Write-Host "Deleting scheduled task: $taskName"
    schtasks /Delete /TN $taskName /F
}

Confirm-And-Delete $collectorTaskName
Confirm-And-Delete $reportTaskName

Write-Host "Done."
