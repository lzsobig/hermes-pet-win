@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Hermes Pet Win - AI Desktop Companion
echo ========================================
echo.

set PYTHON=C:\Python312\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Python not found at %PYTHON%
    echo Please install Python 3.8+ or update PYTHON path in this file
    pause
    exit /b 1
)

echo [1/2] Installing dependencies...
"%PYTHON%" -m pip install -r requirements.txt -q -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

echo [2/2] Starting Hermes Pet...
echo.
cd /d "%~dp0"
"%PYTHON%" main.py

pause
