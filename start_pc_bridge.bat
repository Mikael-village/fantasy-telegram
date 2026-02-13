@echo off
title Fantasy Dashboard - PC Bridge
cd /d %~dp0

echo ========================================
echo   Fantasy Dashboard - PC Bridge
echo ========================================
echo.
echo Connecting to VPS...
echo.

python pc_bridge.py

pause
