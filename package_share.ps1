Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$exePath = Join-Path $projectRoot "dist\quiz_formatter.exe"
if (-not (Test-Path $exePath)) {
    throw "Executable not found. Build it first with .\build_exe.ps1"
}

$pdf = Get-ChildItem -Path $projectRoot -Filter *.pdf | Select-Object -First 1
if (-not $pdf) {
    throw "No PDF file was found in the project root."
}

$releaseRoot = Join-Path $projectRoot "release"
$bundleName = "quiz_formatter_portable"
$bundleDir = Join-Path $releaseRoot $bundleName
$zipPath = Join-Path $releaseRoot "$bundleName.zip"

if (Test-Path $bundleDir) {
    Remove-Item -Recurse -Force $bundleDir
}

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

New-Item -ItemType Directory -Path $bundleDir | Out-Null

Copy-Item $exePath (Join-Path $bundleDir "quiz_formatter.exe")
Copy-Item $pdf.FullName (Join-Path $bundleDir $pdf.Name)

$readme = @"
Quiz Formatter With ChatGPT

Included files:
- quiz_formatter.exe
- $($pdf.Name)

Run the terminal quiz:
1. Unzip the archive anywhere.
2. Double-click "Run Quiz.cmd"
   or open PowerShell in this folder and run:
   .\quiz_formatter.exe

Run the web version:
1. Double-click "Run Web UI.cmd"
   or run:
   .\quiz_formatter.exe --web --port 8000
2. Open this address in your browser:
   http://127.0.0.1:8000

Notes:
- Python is not required.
- Quiz history is stored in the .quiz-cache folder next to the exe.
- Windows SmartScreen may show a warning because this exe is not code-signed.
"@

Set-Content -Path (Join-Path $bundleDir "README.txt") -Value $readme -Encoding UTF8

$terminalLauncher = @"
@echo off
cd /d "%~dp0"
quiz_formatter.exe
pause
"@

Set-Content -Path (Join-Path $bundleDir "Run Quiz.cmd") -Value $terminalLauncher -Encoding ASCII

$webLauncher = @"
@echo off
cd /d "%~dp0"
start "" http://127.0.0.1:8000
quiz_formatter.exe --web --port 8000
pause
"@

Set-Content -Path (Join-Path $bundleDir "Run Web UI.cmd") -Value $webLauncher -Encoding ASCII

Compress-Archive -Path (Join-Path $bundleDir "*") -DestinationPath $zipPath

Write-Host ""
Write-Host "Shareable bundle created:"
Write-Host "  $zipPath"
