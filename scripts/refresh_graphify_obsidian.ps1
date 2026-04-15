param(
    [string]$GraphifyExe = "$env:APPDATA\Python\Python313\Scripts\graphify.exe"
)

if (-not (Test-Path $GraphifyExe)) {
    Write-Error "graphify.exe was not found at '$GraphifyExe'."
    exit 1
}

& $GraphifyExe update .
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python scripts/export_graphify_obsidian.py
exit $LASTEXITCODE
