@echo off
title FinanceKit
echo.
echo  ================================================
echo     FinanceKit - Personal Finance Toolkit
echo  ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.11+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: Launch as desktop app (native window, no browser needed)
cd /d "%~dp0"
python run_app.py
if errorlevel 1 (
    echo.
    echo  FinanceKit requires Python 3.11+. Download from python.org
    echo.
    pause
)
