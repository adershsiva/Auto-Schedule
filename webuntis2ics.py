"""
WebUntis Public Timetable to ICS Converter
Converts public WebUntis timetables into standard .ics calendar files.
Zero external dependencies (uses standard Python library).
"""

import sys
import re
import json
import urllib.request
import urllib.parse
import http.cookiejar
from datetime import datetime, timedelta, timezone

ENTITY_TYPE_MAP = {
    "class": 1,
    "klasse": 1,
    "teacher": 2,
    "lehrer": 2,
    "subject": 3,
    "fach": 3,
    "room": 4,
    "raum": 4,
    "student": 5,
    "schueler": 5,
}

VTIMEZONE_BERLIN = """BEGIN:VTIMEZONE
TZID:Europe/Berlin
X-LIC-LOCATION:Europe/Berlin
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""

def parse_webuntis_url(url: str):
    """
    Extracts base_url, school, entity_type, entity_id, and start_date from a WebUntis public timetable link.
    Example URL:
    https://othr.webuntis.com/WebUntis?school=othr#/basic/timetablePublic/class?date=2026-11-02&entityId=44402
    """
    parsed = urllib.parse.urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Query parameters from main URL (e.g., ?school=othr)
    query_params = urllib.parse.parse_qs(parsed.query)
    school = query_params.get("school", [None])[0]

    # Fragment parameters (e.g. #/basic/timetablePublic/class?date=...&entityId=...)
    fragment = parsed.fragment
    entity_type = 1  # default class
    entity_id = None
    start_date = None

    if fragment:
        # Check entity type in path
        for name, code in ENTITY_TYPE_MAP.items():
            if f"/timetablePublic/{name}" in fragment or f"/timetable/{name}" in fragment:
                entity_type = code
                break
        
        # Parse query params within fragment
        if "?" in fragment:
            frag_query = fragment.split("?", 1)[1]
            frag_params = urllib.parse.parse_qs(frag_query)
            if "entityId" in frag_params:
                entity_id = int(frag_params["entityId"][0])
            if "date" in frag_params:
                start_date = frag_params["date"][0]
            if "school" in frag_params and not school:
                school = frag_params["school"][0]

    if not school:
        raise ValueError("Could not find 'school' parameter in URL.")
    if not entity_id:
        raise ValueError("Could not find 'entityId' parameter in URL.")
    if not start_date:
        # Default to today's date
        start_date = datetime.now().strftime("%Y-%m-%d")

    return {
        "base_url": base_url,
        "school": school,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "start_date": start_date,
    }

class WebUntisClient:
    def __init__(self, base_url: str, school: str):
        self.base_url = base_url.rstrip("/")
        self.school = school
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        self._init_session()

    def _init_session(self):
        """Initializes session cookies by visiting the school portal page."""
        init_url = f"{self.base_url}/WebUntis/?school={urllib.parse.quote(self.school)}"
        req = urllib.request.Request(init_url, headers=self.headers)
        with self.opener.open(req) as resp:
            resp.read()

    def fetch_week(self, entity_type: int, entity_id: int, date_str: str):
        """
        Fetches timetable for a single week given a date (YYYY-MM-DD).
        """
        api_url = (
            f"{self.base_url}/WebUntis/api/public/timetable/weekly/data"
            f"?elementType={entity_type}&elementId={entity_id}&date={date_str}&formatId=3"
        )
        req = urllib.request.Request(api_url, headers=self.headers)
        with self.opener.open(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        result_data = data.get("data", {}).get("result", {}).get("data", {})
        return result_data

def escape_ics(text: str) -> str:
    """Escapes special characters for iCalendar format."""
    if not text:
        return ""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\r\n", "\\n").replace("\n", "\\n")
    return text

def format_display_name(name: str, long_name: str) -> str:
    if not name and not long_name:
        return ""
    if not long_name or long_name == name:
        return name
    if not name:
        return long_name
    if long_name.startswith(name):
        return long_name
    return f"{name} ({long_name})"

def convert_to_ics(all_periods: list, elements_map: dict, calendar_name: str = "WebUntis Timetable", group_filter: str = None, reminder_minutes: int = 15) -> str:
    """
    Builds an RFC 5545 compliant .ics string from periods and elements.
    If group_filter is specified (e.g. '1'), periods for other specific numbered groups (e.g. '_2') are excluded.
    If reminder_minutes is > 0, adds a VALARM reminder trigger before each event.
    """
    now_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//WebUntis2ICS//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ics(calendar_name)}",
        "X-WR-TIMEZONE:Europe/Berlin",
        VTIMEZONE_BERLIN,
    ]

    seen_ids = set()

    for period in all_periods:
        period_id = period.get("id")
        if period_id in seen_ids:
            continue
        seen_ids.add(period_id)

        student_group = period.get("studentGroup", "") or ""
        # Group filtering logic (e.g., if group '1' is selected, ignore groups like '..._2')
        if group_filter:
            group_match = re.search(r'_(\d+)$', student_group)
            if group_match and group_match.group(1) != str(group_filter):
                continue

        date_val = str(period.get("date"))  # e.g. 20261105
        start_time_val = str(period.get("startTime")).zfill(4)  # e.g. 815 -> 0815
        end_time_val = str(period.get("endTime")).zfill(4)  # e.g. 945 -> 0945

        dtstart = f"{date_val}T{start_time_val}00"
        dtend = f"{date_val}T{end_time_val}00"

        # Resolve elements
        subjects = []
        teachers = []
        rooms = []
        classes = []

        for el_ref in period.get("elements", []):
            el_type = el_ref.get("type")
            el_id = el_ref.get("id")
            el_info = elements_map.get((el_type, el_id), {})
            name = el_info.get("name", "")
            long_name = el_info.get("longName", "")

            display = format_display_name(name, long_name)

            if el_type == 1:
                classes.append(display)
            elif el_type == 2:
                teachers.append(display)
            elif el_type == 3:
                subjects.append(display)
            elif el_type == 4:
                rooms.append(display)

        # Title / Summary
        summary = ", ".join(subjects) if subjects else "Class"
        
        # Check cancellation
        is_cancelled = period.get("cellState") == "CANCELLED" or period.get("code") == "CANCELLED"
        if is_cancelled:
            summary = f"[CANCELLED] {summary}"

        # Location
        location = ", ".join(rooms) if rooms else ""

        # Description
        desc_parts = []
        if subjects:
            desc_parts.append(f"Subject: {', '.join(subjects)}")
        if teachers:
            desc_parts.append(f"Lecturer: {', '.join(teachers)}")
        if rooms:
            desc_parts.append(f"Room: {', '.join(rooms)}")
        if classes:
            desc_parts.append(f"Class: {', '.join(classes)}")
        if student_group:
            desc_parts.append(f"Group: {student_group}")
        if period.get("substText"):
            desc_parts.append(f"Note: {period.get('substText')}")
        if period.get("lessonText"):
            desc_parts.append(f"Lesson info: {period.get('lessonText')}")

        description = "\n".join(desc_parts)

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:untis-{period_id}@webuntis")
        lines.append(f"DTSTAMP:{now_stamp}")
        lines.append(f"DTSTART;TZID=Europe/Berlin:{dtstart}")
        lines.append(f"DTEND;TZID=Europe/Berlin:{dtend}")
        lines.append(f"SUMMARY:{escape_ics(summary)}")
        if location:
            lines.append(f"LOCATION:{escape_ics(location)}")
        if description:
            lines.append(f"DESCRIPTION:{escape_ics(description)}")
        if is_cancelled:
            lines.append("STATUS:CANCELLED")
        else:
            lines.append("STATUS:CONFIRMED")
        if not is_cancelled and reminder_minutes and reminder_minutes > 0:
            lines.append("BEGIN:VALARM")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:{escape_ics(summary)}")
            lines.append(f"TRIGGER:-PT{int(reminder_minutes)}M")
            lines.append("END:VALARM")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

def fetch_calendar_ics(url: str, weeks: int = 15, group: str = None, reminder_minutes: int = 15) -> tuple[str, str]:
    """
    Fetches the timetable and returns (ics_content_string, class_name).
    """
    info = parse_webuntis_url(url)
    client = WebUntisClient(info["base_url"], info["school"])

    start_dt = datetime.strptime(info["start_date"], "%Y-%m-%d")
    start_monday = start_dt - timedelta(days=start_dt.weekday())

    all_periods = []
    elements_map = {}
    target_class_name = None

    for w in range(weeks):
        current_monday = start_monday + timedelta(weeks=w)
        date_str = current_monday.strftime("%Y-%m-%d")

        result_data = client.fetch_week(info["entity_type"], info["entity_id"], date_str)
        
        # Cache elements
        for el in result_data.get("elements", []):
            elements_map[(el.get("type"), el.get("id"))] = el
            if el.get("type") == info["entity_type"] and el.get("id") == info["entity_id"]:
                target_class_name = el.get("name") or el.get("longName")

        # Extract periods
        element_periods = result_data.get("elementPeriods", {})
        periods = element_periods.get(str(info["entity_id"]), [])
        if not periods and element_periods:
            periods = list(element_periods.values())[0]

        all_periods.extend(periods)

    cal_name = f"WebUntis - {target_class_name or info['entity_id']}"
    if group:
        cal_name += f" (Group {group})"

    ics_content = convert_to_ics(all_periods, elements_map, calendar_name=cal_name, group_filter=group, reminder_minutes=reminder_minutes)
    return ics_content, target_class_name or str(info['entity_id'])

def sync_timetable(url: str, weeks: int = 15, output_filename: str = None, group: str = None, reminder_minutes: int = 15):
    print(f"Fetching timetable ({weeks} weeks)...")
    ics_content, class_name = fetch_calendar_ics(url, weeks=weeks, group=group, reminder_minutes=reminder_minutes)

    if not output_filename:
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', class_name)
        group_suffix = f"_group{group}" if group else ""
        output_filename = f"timetable_{safe_name}{group_suffix}.ics"

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(ics_content)

    print(f"Successfully generated calendar file: {output_filename}")
    print(f"Total unique events: {ics_content.count('BEGIN:VEVENT')}")
    print(f"File path: {output_filename}")
    print(f"You can now open '{output_filename}' to import it into Google Calendar, Apple Calendar, or Outlook.")
    return output_filename

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert WebUntis public timetable link to .ics calendar file.")
    parser.add_argument("url", nargs="?", help="WebUntis public timetable URL")
    parser.add_argument("-w", "--weeks", type=int, default=15, help="Number of weeks to fetch (default: 15)")
    parser.add_argument("-o", "--output", help="Output .ics file name")
    parser.add_argument("-g", "--group", help="Filter for student group number (e.g. '1' for Group 1 only)")
    parser.add_argument("-r", "--reminder", type=int, default=15, help="Notification alert in minutes before class (default: 15, 0 to disable)")

    args = parser.parse_args()

    if not args.url:
        print("=" * 50)
        print(" WebUntis Public Timetable to .ICS Converter")
        print("=" * 50)
        args.url = input("Paste your WebUntis timetable URL: ").strip()
        if not args.url:
            print("Error: No URL provided.")
            sys.exit(1)
        weeks_input = input("Number of weeks to fetch (press Enter for 15): ").strip()
        if weeks_input.isdigit():
            args.weeks = int(weeks_input)
        group_input = input("Filter specific lab/practical group (e.g. 1 or 2, press Enter for all): ").strip()
        if group_input:
            args.group = group_input
        reminder_input = input("Alert reminder in minutes before class (press Enter for 15, 0 for none): ").strip()
        if reminder_input.isdigit():
            args.reminder = int(reminder_input)

    sync_timetable(args.url, weeks=args.weeks, output_filename=args.output, group=args.group, reminder_minutes=args.reminder)
