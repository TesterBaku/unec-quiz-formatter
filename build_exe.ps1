Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Virtual environment not found. Create .venv first."
}

& $python -m PyInstaller --clean --noconfirm quiz_formatter.spec

Write-Host ""
Write-Host "Build complete. Share the executable at:"
Write-Host "  $projectRoot\dist\quiz_formatter.exe"
