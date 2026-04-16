param(
    [string]$GraphifyExe = ""
)

function Resolve-GraphifyExe {
    param(
        [string]$PreferredPath
    )

    if ($PreferredPath -and (Test-Path $PreferredPath)) {
        return (Resolve-Path $PreferredPath).Path
    }

    $command = Get-Command graphify -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
        return $command.Source
    }

    $candidates = @(
        "$env:APPDATA\Python\Python313\Scripts\graphify.exe",
        "$env:APPDATA\Python\Python312\Scripts\graphify.exe",
        "$env:APPDATA\Python\Python311\Scripts\graphify.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\Scripts\graphify.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\graphify.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts\graphify.exe"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

$resolvedGraphifyExe = Resolve-GraphifyExe -PreferredPath $GraphifyExe
if (-not $resolvedGraphifyExe) {
    Write-Error "graphify.exe was not found. Install Graphify or pass -GraphifyExe with an explicit path."
    exit 1
}

& $resolvedGraphifyExe update .
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python scripts/export_graphify_obsidian.py
exit $LASTEXITCODE
