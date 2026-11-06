"""
Automated validation tests for WebUntis to .ICS generator.
Run: python test_suite.py
"""

import os
import unittest
from webuntis2ics import parse_webuntis_url, convert_to_ics, format_display_name

class TestWebUntis2ICS(unittest.TestCase):

    def test_url_parser(self):
        url = "https://othr.webuntis.com/WebUntis?school=othr#/basic/timetablePublic/class?date=2026-11-02&entityId=44402"
        info = parse_webuntis_url(url)
        self.assertEqual(info["base_url"], "https://othr.webuntis.com")
        self.assertEqual(info["school"], "othr")
        self.assertEqual(info["entity_type"], 1)
        self.assertEqual(info["entity_id"], 44402)
        self.assertEqual(info["start_date"], "2026-11-02")
        print(" [PASS] URL parser extracts all parameters correctly.")

    def test_display_name_formatting(self):
        # Case 1: name is short, long_name starts with name
        self.assertEqual(format_display_name("P123", "P123 (Hörsaal)"), "P123 (Hörsaal)")
        # Case 2: different names
        self.assertEqual(format_display_name("IM_OS", "Betriebssysteme"), "IM_OS (Betriebssysteme)")
        # Case 3: identical
        self.assertEqual(format_display_name("ICS3", "ICS3"), "ICS3")
        print(" [PASS] Display name formatting handles short & long names cleanly.")

    def test_ics_generation_and_group_filter(self):
        sample_elements = {
            (1, 44402): {"type": 1, "id": 44402, "name": "ICS3", "longName": "Bachelor ICS3"},
            (2, 22678): {"type": 2, "id": 22678, "name": "Kaa", "longName": ""},
            (3, 5268): {"type": 3, "id": 5268, "name": "IM_OS", "longName": "Betriebssysteme"},
            (4, 1240): {"type": 4, "id": 1240, "name": "P123", "longName": "P123 (Hörsaal - 56 - SG)"},
        }

        sample_periods = [
            # Event 1: Shared class
            {
                "id": 101,
                "date": 20261102,
                "startTime": 815,
                "endTime": 945,
                "studentGroup": "IM_OS_ICS3",
                "elements": [{"type": 1, "id": 44402}, {"type": 3, "id": 5268}, {"type": 4, "id": 1240}],
            },
            # Event 2: Group 1 only
            {
                "id": 102,
                "date": 20261103,
                "startTime": 1000,
                "endTime": 1130,
                "studentGroup": "IM_OS_ICS3_1",
                "elements": [{"type": 1, "id": 44402}, {"type": 3, "id": 5268}],
            },
            # Event 3: Group 2 only
            {
                "id": 103,
                "date": 20261103,
                "startTime": 1000,
                "endTime": 1130,
                "studentGroup": "IM_OS_ICS3_2",
                "elements": [{"type": 1, "id": 44402}, {"type": 3, "id": 5268}],
            },
        ]

        # All groups
        ics_all = convert_to_ics(sample_periods, sample_elements)
        self.assertEqual(ics_all.count("BEGIN:VEVENT"), 3)
        self.assertIn("BEGIN:VCALENDAR", ics_all)
        self.assertIn("END:VCALENDAR", ics_all)
        self.assertIn("TZID=Europe/Berlin:20261102T081500", ics_all)
        print(" [PASS] Calendar generation produces valid RFC 5545 format.")

        # Group 1 filter: should include Event 1 (all) + Event 2 (Group 1), but exclude Event 3 (Group 2)
        ics_g1 = convert_to_ics(sample_periods, sample_elements, group_filter="1")
        self.assertEqual(ics_g1.count("BEGIN:VEVENT"), 2)
        self.assertIn("untis-101@webuntis", ics_g1)
        self.assertIn("untis-102@webuntis", ics_g1)
        self.assertNotIn("untis-103@webuntis", ics_g1)
        print(" [PASS] Group filter successfully isolates student groups.")

    def test_existing_calendar_files(self):
        self.assertTrue(os.path.exists("timetable_ICS3.ics"), "timetable_ICS3.ics file should exist.")
        with open("timetable_ICS3.ics", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertIn("END:VCALENDAR", content)
        self.assertGreater(content.count("BEGIN:VEVENT"), 10)
        print(f" [PASS] Existing timetable_ICS3.ics verified ({content.count('BEGIN:VEVENT')} events found).")

if __name__ == "__main__":
    unittest.main()

