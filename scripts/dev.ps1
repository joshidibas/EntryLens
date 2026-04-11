param()

$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $workspaceRoot "entrylens-api"
$frontendDir = Join-Path $workspaceRoot "entrylens-frontend"

$apiJob = Start-Job -Name "entrylens-api" -ScriptBlock {
    param($Dir)
    Set-Location $Dir
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} -ArgumentList $apiDir

$frontendJob = Start-Job -Name "entrylens-frontend" -ScriptBlock {
    param($Dir)
    Set-Location $Dir
    npm run dev -- --host 127.0.0.1 --port 5173
} -ArgumentList $frontendDir

$jobs = @($apiJob, $frontendJob)

Write-Host "EntryLens dev environment is starting..."
Write-Host "API: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Press Ctrl+C to stop both jobs."

try {
    while ($true) {
        foreach ($job in $jobs) {
            Receive-Job -Job $job -Keep | Out-Host
        }

        $failedJob = $jobs | Where-Object { $_.State -in @("Failed", "Stopped", "Completed") } | Select-Object -First 1
        if ($null -ne $failedJob -and $failedJob.State -ne "Running") {
            throw "Background job '$($failedJob.Name)' exited with state $($failedJob.State)."
        }

        Start-Sleep -Milliseconds 500
    }
}
finally {
    foreach ($job in $jobs) {
        if ($job.State -eq "Running") {
            Stop-Job -Job $job | Out-Null
        }
        Receive-Job -Job $job -Keep | Out-Host
        Remove-Job -Job $job -Force | Out-Null
    }
}
