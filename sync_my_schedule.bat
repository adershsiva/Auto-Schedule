@echo off
title WebUntis Sync
echo ========================================================
echo  Syncing OTHR Timetable (ICS3) to .ICS Calendar
echo ========================================================
echo.
python webuntis2ics.py "https://othr.webuntis.com/WebUntis?school=othr#/basic/timetablePublic/class?date=2026-11-02&entityId=44402" -w 15
echo.
echo ========================================================
echo  Finished! Calendar file updated.
echo ========================================================
pause

