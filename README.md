# WebUntis to iCal (.ics)

A simple Python project to convert public WebUntis timetables into a `.ics` calendar file so you can import your classes into Google Calendar, Apple Calendar, or Outlook.

## Why?

WebUntis doesn't provide an export or download button for public timetable links (like the ones used at OTH Regensburg and many other universities). I built this so I could easily put my semester schedule into my phone's calendar without typing everything in manually.

## What it does

- Takes any public WebUntis timetable link and downloads the schedule as a standard `.ics` file.
- Uses only Python built-in libraries (no `pip install` needed).
- Fetches the whole semester (e.g. 15 weeks) at once.
- Shows course names, lecture rooms, lecturers, and notes.
- Lets you filter by lab / practical group (e.g. Group 1 vs Group 2).

## How to use

### Option 1: Run the script directly
Run the Python script with your WebUntis link:

```bash
python webuntis2ics.py "YOUR_WEBUNTIS_LINK"
```

Example:
```bash
python webuntis2ics.py "https://othr.webuntis.com/WebUntis?school=othr#/basic/timetablePublic/class?date=2026-11-02&entityId=44402"
```

Helpful options:
- `-w 15`: Number of weeks to fetch (default is 15 weeks).
- `-g 1`: Filter for a specific practical group (e.g. Group 1).
- `-o my_schedule.ics`: Set a custom file name.

### Option 2: Using the simple web page
If you don't want to use the command line:

```bash
python app.py
```
Then open `http://localhost:8000` in your browser, paste your link, and click Download.

## How to add to your calendar

- **Google Calendar**: Go to Settings -> Import & Export -> Import, and choose the generated `.ics` file.
- **Apple Calendar**: Just double-click the `.ics` file on your Mac or iPhone.
- **Outlook**: Double-click the `.ics` file or drag it into Outlook.

## Automatic updates via GitHub Actions

This repository includes a GitHub Action (`.github/workflows/sync.yml`) that runs every morning and automatically updates the `.ics` calendar files.

You can subscribe to the raw link in Google Calendar (*Other calendars -> From URL*) or Apple Calendar so your schedule updates automatically:

- **All Groups**:  
  `https://raw.githubusercontent.com/adershsiva/Auto-Schedule/main/timetable_ICS3.ics`
- **Group 1 Only**:  
  `https://raw.githubusercontent.com/adershsiva/Auto-Schedule/main/timetable_ICS3_group1.ics`
