"""
WebUntis to .ICS Web Downloader & Live Calendar Feed
Run: python app.py
Open: http://localhost:8000 in your browser to download or subscribe to your calendar.
"""

import http.server
import socketserver
import urllib.parse
import re
from webuntis2ics import fetch_calendar_ics

PORT = 8000

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebUntis .ICS Calendar Downloader</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --secondary: #0f766e;
            --secondary-hover: #115e59;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #16a34a;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            width: 100%;
            max-width: 620px;
            background: var(--card);
            border-radius: 16px;
            padding: 36px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
        }
        h1 {
            font-size: 24px;
            margin-top: 0;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        p.subtitle {
            color: var(--text-muted);
            margin-bottom: 24px;
            font-size: 14px;
            line-height: 1.5;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 6px;
            color: #334155;
        }
        input, select {
            width: 100%;
            padding: 12px 14px;
            font-size: 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            box-sizing: border-box;
            background: #fff;
            transition: border-color 0.15s ease;
        }
        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }
        .row {
            display: flex;
            gap: 16px;
        }
        .row .form-group {
            flex: 1;
        }
        .button-group {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 10px;
        }
        .btn {
            width: 100%;
            padding: 14px 20px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            text-decoration: none;
            box-sizing: border-box;
            transition: all 0.2s;
        }
        .btn-download {
            background: var(--primary);
            color: white;
        }
        .btn-download:hover {
            background: var(--primary-hover);
        }
        .btn-subscribe {
            background: #f1f5f9;
            color: #334155;
            border: 1px solid var(--border);
        }
        .btn-subscribe:hover {
            background: #e2e8f0;
            color: #0f172a;
        }
        .helper-text {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }
        .copy-box {
            margin-top: 20px;
            background: #f8fafc;
            border: 1px dashed var(--border);
            border-radius: 8px;
            padding: 14px;
            font-size: 13px;
        }
        .copy-box code {
            display: block;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 8px 10px;
            border-radius: 6px;
            font-family: monospace;
            word-break: break-all;
            margin: 6px 0 10px;
            color: #0f766e;
        }
        .instructions {
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            font-size: 13px;
            color: var(--text-muted);
        }
        .instructions ol {
            padding-left: 18px;
            line-height: 1.6;
            margin-top: 6px;
        }
        .badge {
            background: #dcfce7;
            color: #15803d;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 12px;
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 WebUntis .ICS Downloader <span class="badge">Live</span></h1>
        <p class="subtitle">Convert any public WebUntis timetable into an <code>.ics</code> calendar file for Google Calendar, Apple Calendar, or Outlook.</p>

        <form id="timetableForm" action="/download" method="GET">
            <div class="form-group">
                <label for="url">WebUntis Public Timetable URL</label>
                <input 
                    type="url" 
                    id="url" 
                    name="url" 
                    required 
                    placeholder="https://othr.webuntis.com/WebUntis?school=othr#/basic/timetablePublic/class?..."
                    value="https://othr.webuntis.com/WebUntis?school=othr#/basic/timetablePublic/class?date=2026-11-02&entityId=44402"
                    oninput="updateLinks()"
                >
                <div class="helper-text">Supports class, teacher, subject, or room public links.</div>
            </div>

            <div class="row">
                <div class="form-group">
                    <label for="weeks">Weeks</label>
                    <input type="number" id="weeks" name="weeks" value="15" min="1" max="30" oninput="updateLinks()">
                </div>
                <div class="form-group">
                    <label for="group">Lab Group</label>
                    <input type="text" id="group" name="group" placeholder="e.g. 1 (optional)" oninput="updateLinks()">
                </div>
                <div class="form-group">
                    <label for="reminder">Alert (Mins)</label>
                    <input type="number" id="reminder" name="reminder" value="15" min="0" max="120" oninput="updateLinks()">
                </div>
            </div>

            <div class="button-group">
                <button type="submit" class="btn btn-download">
                    📥 Download Static .ics File
                </button>
                <a id="subscribeBtn" href="#" class="btn btn-subscribe">
                    🗓️ One-Click Subscribe (Apple Calendar / Outlook)
                </a>
            </div>
        </form>

        <div class="copy-box">
            <strong>🔗 Live Subscription Feed URL (Auto-syncs):</strong>
            <div class="helper-text">Add this as a "Subscription Calendar" in Google Calendar or your phone:</div>
            <code id="feedUrlText">Loading...</code>
            <button type="button" class="btn btn-subscribe" style="padding: 6px 12px; font-size: 13px;" onclick="copyFeedUrl()">
                📋 Copy Subscription URL
            </button>
        </div>

        <div class="instructions">
            <strong>How to use:</strong>
            <ol>
                <li><strong>Static Download:</strong> Click <em>Download Static .ics File</em> to get the file, then open it in Apple Calendar, Outlook, or import to Google Calendar.</li>
                <li><strong>Live Auto-Updating Sync:</strong> Copy the Subscription URL and in Google Calendar click <em>+ → From URL</em>. Your calendar will automatically sync changes!</li>
            </ol>
        </div>
    </div>

    <script>
        function getQueryString() {
            const url = encodeURIComponent(document.getElementById('url').value.trim());
            const weeks = document.getElementById('weeks').value.trim() || '15';
            const group = encodeURIComponent(document.getElementById('group').value.trim());
            let qs = `?url=${url}&weeks=${weeks}`;
            if (group) qs += `&group=${group}`;
            return qs;
        }

        function updateLinks() {
            const qs = getQueryString();
            const host = window.location.host;
            const fullHttp = `${window.location.protocol}//${host}/calendar.ics${qs}`;
            const fullWebcal = `webcal://${host}/calendar.ics${qs}`;

            document.getElementById('subscribeBtn').href = fullWebcal;
            document.getElementById('feedUrlText').innerText = fullHttp;
        }

        function copyFeedUrl() {
            const text = document.getElementById('feedUrlText').innerText;
            navigator.clipboard.writeText(text).then(() => {
                alert("Copied subscription URL to clipboard! Paste it into Google Calendar (+ -> From URL).");
            });
        }

        window.onload = updateLinks;
    </script>
</body>
</html>
"""

class TimetableHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        elif parsed.path == "/download" or parsed.path == "/calendar.ics":
            params = urllib.parse.parse_qs(parsed.query)
            target_url = params.get("url", [None])[0]
            weeks = int(params.get("weeks", [15])[0])
            group = params.get("group", [None])[0]
            if group and group.strip() == "":
                group = None

            if not target_url:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Error: Missing 'url' parameter.")
                return

            try:
                ics_data, class_name = fetch_calendar_ics(target_url, weeks=weeks, group=group)
                safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', class_name)
                group_suffix = f"_group{group}" if group else ""
                filename = f"timetable_{safe_name}{group_suffix}.ics"

                self.send_response(200)
                self.send_header("Content-Type", "text/calendar; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.end_headers()
                self.wfile.write(ics_data.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"Error fetching timetable: {str(e)}".encode("utf-8"))
            return

        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    # Allow port reuse so restarting the server does not fail with 'Address already in use'
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), TimetableHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Open http://localhost:8000 in your browser to download or subscribe to your calendar!")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
