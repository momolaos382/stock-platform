@echo off
chcp 65001 >nul
title Stock Platform
REM ================================================
REM  run.bat - DOUBLE-CLICK to start the website
REM  - Already running?  -> just opens the browser
REM  - First run?        -> creates .venv and installs packages (needs internet, a few minutes)
REM  - Keep this window open while using the site. Close it (or press Ctrl+C) to stop.
REM ================================================
cd /d "%~dp0"

REM --- 1) already running on port 8501? just open it ---
netstat -ano | findstr /R /C:":8501 .*LISTENING" >nul
if %errorlevel%==0 (
    echo The website is already running. Opening the browser...
    start "" http://localhost:8501
    timeout /t 3 >nul
    exit /b 0
)

REM --- 2) first run: create the Python environment ---
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] First run: creating Python environment...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Python was not found. Install Python 3.12 from python.org
        echo        and tick "Add python.exe to PATH" during setup, then double-click run.bat again.
        pause
        exit /b 1
    )
)

REM --- 3) install packages only when something is missing ---
".venv\Scripts\python.exe" -c "import streamlit, pandas, scipy, plotly, yfinance, pdfplumber, PIL" >nul 2>nul
if errorlevel 1 (
    echo [2/3] Installing packages - needs internet, takes a few minutes...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: package installation failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

REM --- 4) start. headless = skip Streamlit's "enter your email" first-run question (that is what made it hang) ---
echo [3/3] Starting website...
echo.
echo   On this PC:                http://localhost:8501
echo   Phone / tablet (same Wi-Fi or LAN cable router), use one of these IPv4 addresses with :8501
ipconfig | findstr /C:"IPv4"
echo.
echo   Keep this window open. Close it to stop the website.
echo.
start "" cmd /c "timeout /t 8 >nul & start http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --server.port 8501
echo.
echo The website stopped.
pause