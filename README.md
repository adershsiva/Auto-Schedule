# WebUntis to iCal (.ics) Calendar Downloader

A lightweight, zero-dependency Python project that converts public WebUntis timetable links into standard `.ics` calendar files. Works with **Google Calendar**, **Apple Calendar**, **Microsoft Outlook**, and mobile calendar apps.

Supports both **One-Time Static File Download** and **Live Auto-Updating Calendar Subscriptions**.

---

## ⚡ Quick Start on Windows

- **Double-click [`start_web_app.bat`](file:///d:/Auto-Schedule/start_web_app.bat)**: Automatically opens the web downloader at `http://localhost:8000` in your browser.
- **Double-click [`sync_my_schedule.bat`](file:///d:/Auto-Schedule/sync_my_schedule.bat)**: Instantly fetches 15 weeks for your OTHR class (`ICS3`) and outputs `timetable_ICS3.ics`.

---

## 🚀 How to Use

### 1. Web App Downloader (Recommended)
Launch the built-in local web server:
```powershell
python app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser:
- 📥 **Download Static `.ics`**: One click downloads the `.ics` directly into your browser's Downloads folder.
- 🗓️ **One-Click Subscribe**: Subscribes directly into Apple Calendar or Outlook with auto-sync.
- 📋 **Copy Subscription URL**: Paste the link into Google Calendar (*Other calendars → From URL*) to have your classes stay automatically synchronized.

---

### 2. Command Line / Direct Script
Run the script directly from your terminal:
```powershell
python webuntis2ics.py "https://othr.webuntis.com/WebUntis?school=othr#/basic/timetablePublic/class?date=2026-11-02&entityId=44402"
```

#### CLI Options
```text
options:
  -h, --help           Show help message and exit
  -w, --weeks WEEKS    Number of weeks to fetch (default: 15)
  -o, --output OUTPUT  Custom output .ics filename
  -g, --group GROUP    Filter for student group (e.g. '1' for Group 1 only)
```

**Examples:**
```powershell
# Fetch 15 weeks for entire semester
python webuntis2ics.py "https://..." -w 15

# Fetch only for practical / lab group 1
python webuntis2ics.py "https://..." -w 15 -g 1
```

---

## 🧪 Testing the Project

Run the included automated test suite:
```powershell
python test_suite.py
```

---

## 📅 How to Import into Calendar Apps

### Apple Calendar (macOS / iPhone / iPad)
- **Static:** Double-click the downloaded `.ics` file.
- **Live Sync:** In Apple Calendar on Mac, choose **File → New Calendar Subscription**, paste your feed URL, and set auto-refresh to *Every day* or *Every hour*.

### Google Calendar
- **Static Import:** Go to [Google Calendar](https://calendar.google.com/) → **Settings** (Gear icon) → **Import & Export** → upload the `.ics` file.
- **Live Sync:** Under *Other calendars* on the left sidebar, click **+** → **From URL**, paste the subscription link, and click **Add calendar**.

### Microsoft Outlook
- **Static:** Double-click the `.ics` file or drag it into Outlook.
- **Live Sync:** Go to Calendar → **Add Calendar** → **Subscribe from web** → paste the URL.

---

## 🐳 Docker Deployment (Optional)

Build and run anywhere with Docker:
```bash
docker build -t webuntis2ics .
docker run -p 8000:8000 webuntis2ics
```
