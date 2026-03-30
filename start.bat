@echo off
title FinanceKit - Starting...
echo.
echo  ================================================
echo     FinanceKit - Personal Finance Toolkit
echo  ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.10+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist ".deps_installed" (
    echo  Installing dependencies (first time only)...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to install dependencies.
        echo  Try running: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo. > .deps_installed
    echo.
    echo  Dependencies installed successfully!
    echo.
)

echo  Starting FinanceKit...
echo  The app will open in your browser automatically.
echo  To stop, close this window or press Ctrl+C.
echo.
python -m streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
pause
