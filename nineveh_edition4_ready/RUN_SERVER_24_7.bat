@echo off
title Nineveh Film Festival 24/7 Server
cd /d "%~dp0"
echo ========================================================
echo Starting Nineveh Film Festival 24/7 Watchdog Server...
echo ========================================================
python keep_alive.py
pause
