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

:: Launch via launcher.py (handles deps, server, tray icon, browser)
python launcher.py
pause
