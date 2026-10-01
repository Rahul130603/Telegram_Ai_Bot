@echo off
setlocal

title Telegram AI Auto Post Bot
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [ERROR] Python virtual environment not found.
    echo First run backend\scripts\setup.ps1 from PowerShell.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo.
    echo [ERROR] backend\.env file not found.
    echo Copy .env.example to .env and add credentials privately.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Telegram AI Auto Post Bot
echo ========================================
echo Backend : http://127.0.0.1:8000
echo Health  : http://127.0.0.1:8000/healthz
echo Stop    : Press Ctrl+C
echo ========================================
echo.

".venv\Scripts\python.exe" -m app

set "BOT_EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%BOT_EXIT_CODE%"=="0" (
    echo [ERROR] Server stopped with exit code %BOT_EXIT_CODE%.
) else (
    echo Server stopped.
)
echo.
pause
exit /b %BOT_EXIT_CODE%
