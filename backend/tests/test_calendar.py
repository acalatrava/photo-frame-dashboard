import http.server
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.services.calendar.service import parse_ics
from tests.helpers import set_config, wait_for

MAD = ZoneInfo("Europe/Madrid")

ICS = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//EN
BEGIN:VTIMEZONE
TZID:Europe/Madrid
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
END:VTIMEZONE
BEGIN:VEVENT
UID:weekly-1
SUMMARY:Reunion semanal
DTSTART;TZID=Europe/Madrid:20261012T090000
DTEND;TZID=Europe/Madrid:20261012T100000
RRULE:FREQ=WEEKLY;BYDAY=MO
END:VEVENT
BEGIN:VEVENT
UID:allday-1
SUMMARY:Puente
DTSTART;VALUE=DATE:20261030
DTEND;VALUE=DATE:20261102
END:VEVENT
BEGIN:VEVENT
UID:utc-1
SUMMARY:Llamada UTC
DTSTART:20261026T233000Z
DTEND:20261027T003000Z
END:VEVENT
BEGIN:VEVENT
UID:float-1
SUMMARY:Flotante
DTSTART:20261104T180000
DTEND:20261104T190000
END:VEVENT
END:VCALENDAR
"""


def test_parse_dst_all_day_and_utc():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=MAD)
    evs = parse_ics(ICS, MAD, now=now)
    weekly = sorted((e for e in evs if e["uid"] == "weekly-1"), key=lambda e: e["start"])
    starts = [e["start"] for e in weekly]
    assert "2026-10-19T09:00:00+02:00" in starts
    assert "2026-10-26T09:00:00+01:00" in starts  # after the DST change on 25 Oct, still 09:00 local
    assert all(s[11:16] == "09:00" for s in starts)
    allday = next(e for e in evs if e["uid"] == "allday-1")
    assert allday["all_day"] is True and allday["start"] == "2026-10-30" and allday["end"] == "2026-11-02"
    utc = next(e for e in evs if e["uid"] == "utc-1")
    assert utc["start"] == "2026-10-27T00:30:00+01:00" and utc["all_day"] is False  # 23:30Z -> 00:30 CET
    flt = next(e for e in evs if e["uid"] == "float-1")
    assert flt["start"] == "2026-11-04T18:00:00+01:00"


class _Handler(http.server.BaseHTTPRequestHandler):
    body = ICS
    status = 200

    def do_GET(self):
        self.send_response(self.status)
        self.send_header("Content-Type", "text/calendar")
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *a):
        pass


@pytest.fixture()
def ics_server():
    _Handler.body, _Handler.status = ICS, 200
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, f"http://127.0.0.1:{srv.server_address[1]}/cal.ics"
    srv.shutdown()


def setup_people_and_cal(admin, url):
    set_config(admin,
               people=[{"id": "ana", "name": "Ana", "color": "#2D5BFF"}, {"id": "luis", "name": "Luis", "color": "#FF5B2D"}],
               calendars=[{"id": "fam", "name": "Familia", "type": "ics", "url": url, "person_ids": ["ana"]}])


def test_sync_and_device_view_with_fallback(paired, ics_server):
    admin, dev, token = paired
    srv, url = ics_server
    setup_people_and_cal(admin, url)
    r = admin.post("/api/v1/admin/calendars/fam/sync")
    assert r.status_code == 200, r.text
    h = {"Authorization": f"Bearer {token}"}
    dash = admin.get("/api/v1/device/dashboard", headers=h).json()
    assert dash["events"] and all(e["people"] == ["ana"] for e in dash["events"])
    n = len(dash["events"])
    # provider goes down: events remain (cached) and a notice is raised
    _Handler.status = 500
    assert admin.post("/api/v1/admin/calendars/fam/sync").status_code == 502
    dash = admin.get("/api/v1/device/dashboard", headers=h).json()
    assert len(dash["events"]) == n
    assert any(x["type"] == "calendar" for x in dash["notices"])
    # recovered
    _Handler.status = 200
    assert admin.post("/api/v1/admin/calendars/fam/sync").status_code == 200
    assert not admin.get("/api/v1/device/dashboard", headers=h).json()["notices"]


def test_removed_event_disappears(paired, ics_server):
    admin, dev, token = paired
    srv, url = ics_server
    setup_people_and_cal(admin, url)
    admin.post("/api/v1/admin/calendars/fam/sync")
    h = {"Authorization": f"Bearer {token}"}
    assert any(e["title"] == "Puente" for e in admin.get("/api/v1/device/dashboard", headers=h).json()["events"])
    _Handler.body = ICS.replace(b"SUMMARY:Puente", b"SUMMARY:Puente").split(b"BEGIN:VEVENT\nUID:allday-1")[0] + b"END:VCALENDAR\n"
    admin.post("/api/v1/admin/calendars/fam/sync")
    assert not any(e["title"] == "Puente" for e in admin.get("/api/v1/device/dashboard", headers=h).json()["events"])


def test_invalid_calendar_config_rejected(admin):
    cfg = admin.get("/api/v1/admin/config").json()["config"]
    cfg["calendars"] = [{"id": "x", "name": "x", "type": "ics", "url": "ftp://bad", "person_ids": []}]
    assert admin.put("/api/v1/admin/config", json=cfg).status_code in (400, 422)
