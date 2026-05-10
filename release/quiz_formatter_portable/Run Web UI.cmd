@echo off
cd /d "%~dp0"
start "" http://127.0.0.1:8000
quiz_formatter.exe --web --port 8000
pause
