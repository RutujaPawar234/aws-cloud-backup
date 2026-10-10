@echo off
REM ============================================================
REM  CloudVault - double-click launcher for the desktop app.
REM  No commands needed: just run this file.
REM  Backend URL is read from client\client_config.json.
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating it and installing dependencies...
    py -3 -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --prefer-binary -r requirements.txt
)

echo Starting CloudVault...
".venv\Scripts\python.exe" -m client.main

if errorlevel 1 (
    echo.
    echo The app exited with an error. Press any key to close.
    pause >nul
)
