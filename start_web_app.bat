@echo off
title WebUntis Calendar Downloader
echo Starting WebUntis to .ICS Calendar Web Server...
echo.
start http://localhost:8000
python app.py
pause

