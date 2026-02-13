@echo off
title Fantasy Dashboard - Local Server
cd /d %~dp0

echo ========================================
echo   Fantasy Dashboard - Local Mode
echo ========================================
echo.

REM Запуск сервера
echo Starting server on http://localhost:8000
start "Fantasy Server" cmd /c "python server.py"

REM Ждём запуска сервера
timeout /t 3 /nobreak >nul

REM Запуск туннеля
echo.
echo Starting Cloudflare Tunnel...
echo (URL появится ниже - скопируй его)
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8000

pause
