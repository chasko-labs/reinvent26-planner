import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26.export_week import build_week, session_entry, watcher_latest  # noqa: E402


def _catalog():
    return [
        {"sessionId": "h1", "abbreviation": "STG363", "title": "Storage Talk",
         "startTime": "2026-11-30T08:30:00", "endTime": "2026-11-30T09:30:00",
         "venue": "MGM Grand", "room": "Room 306",
         "speakers": [{"name": "Ann Lee"}], "level": "300"},
        {"sessionId": "f1", "abbreviation": "NET335", "title": "Net Talk",
         "startTime": "2026-11-30T16:00:00", "endTime": "2026-11-30T17:00:00",
         "venue": "MGM Grand", "room": "Room 101",
         "speakers": [{"name": "Bob Ray"}], "level": "200"},
    ]


def _schedule():
    return {"schedule": {
        "reserved": ["h1"],
        "favorites": ["f1"],
        "personalTime": [],
    }}


def test_session_entry_shapes_fields():
    entry = session_entry(_catalog()[0])
    assert entry["code"] == "STG363"
    assert entry["date"] == "2026-11-30"
    assert entry["start"] == "08:30"
    assert entry["speakers"] == ["Ann Lee"]
    assert entry["reservable"] is False


def test_session_entry_marks_reservable():
    item = dict(_catalog()[0])
    item["isReservable"] = True
    item["seatAvailability"] = "limited"
    entry = session_entry(item)
    assert entry["reservable"] is True
    assert entry["seat"] == "limited"


def test_session_entry_carries_format_and_leg_rooms():
    catalog = [
        {"sessionId": "h1", "abbreviation": "AAA111", "title": "First",
         "startTime": "2026-11-30T08:30:00", "endTime": "2026-11-30T09:30:00",
         "venue": "MGM Grand", "room": "Level 3 | Room 350",
         "speakers": [], "level": "300", "sessionType": "Workshop"},
        {"sessionId": "h2", "abbreviation": "BBB222", "title": "Second",
         "startTime": "2026-11-30T11:30:00", "endTime": "2026-11-30T12:30:00",
         "venue": "Caesars Forum", "room": "Octavius 4",
         "speakers": [], "level": "300", "sessionType": "Chalk talk"},
    ]
    assert session_entry(catalog[0])["format"] == "Workshop"
    schedule = {"schedule": {
        "reserved": ["h1", "h2"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    legs = [e for e in week["timeline"] if e["kind"] == "leg"]
    assert len(legs) == 1
    assert legs[0]["from_room"] == "Level 3 | Room 350"
    assert legs[0]["to_room"] == "Octavius 4"


def test_build_week_splits_held_favorites_and_windows(tmp_path):
    week = build_week(_schedule(), _catalog(), str(tmp_path), "2026-11-05")
    assert [held_entry["code"] for held_entry in week["held"]] == ["STG363"]
    assert [f["code"] for f in week["favorites"]] == ["NET335"]
    assert week["windows"] == []
    assert week["watcher"]["report"] is None


def test_build_week_finds_gap_window():
    catalog = _catalog() + [
        {"sessionId": "h2", "abbreviation": "INV530", "title": "Second",
         "startTime": "2026-11-30T11:30:00", "endTime": "2026-11-30T12:30:00",
         "venue": "MGM Grand", "room": "Room 350",
         "speakers": [], "level": "500"},
    ]
    schedule = {"schedule": {
        "reserved": ["h1", "h2"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    assert len(week["windows"]) == 1
    assert week["windows"][0]["start"] == "09:30"
    assert week["windows"][0]["end"] == "11:30"


def test_watcher_latest_reads_added_codes(tmp_path):
    report = ("# new sessions 2026-11-05 (reinvent2026)\n\n"
              "## opportunities (open seat, fits your week)\n\n"
              "- NET341 open seat\n\n"
              "## all added sessions\n\n"
              "- AIM999 new session\n- NET341 new session\n")
    (tmp_path / "new-sessions-2026-11-05.md").write_text(report)
    latest = watcher_latest(str(tmp_path))
    assert latest["report"] == "2026-11-05"
    assert latest["added"] == ["AIM999", "NET341"]
    assert latest["opportunities"] == ["NET341"]


def test_watcher_latest_empty_dir(tmp_path):
    assert watcher_latest(str(tmp_path))["report"] is None


def test_build_week_timeline_interleaves_open_windows():
    catalog = [
        {"sessionId": "h1", "abbreviation": "AAA111", "title": "First",
         "startTime": "2026-11-30T08:30:00", "endTime": "2026-11-30T09:30:00",
         "venue": "MGM Grand", "room": "R1", "speakers": [], "level": "300"},
        {"sessionId": "h2", "abbreviation": "BBB222", "title": "Second",
         "startTime": "2026-11-30T11:30:00", "endTime": "2026-11-30T12:30:00",
         "venue": "MGM Grand", "room": "R2", "speakers": [], "level": "300"},
    ]
    schedule = {"schedule": {
        "reserved": ["h1", "h2"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    kinds = [(e["kind"], e["start"]) for e in week["timeline"]
             if e.get("date") == "2026-11-30"]
    assert kinds == [("meal", ""), ("held", "08:30"), ("leg", "09:30"),
                     ("meal", "09:30"), ("open", "09:30"), ("held", "11:30"),
                     ("meal", "12:30")]
    assert week["timeline"][2]["mode"] == "walk"


def test_build_week_adds_breakfast_lunch_dinner_blocks():
    catalog = [
        {"sessionId": "h1", "abbreviation": "AAA111", "title": "First",
         "startTime": "2026-11-30T08:30:00", "endTime": "2026-11-30T09:30:00",
         "venue": "MGM Grand", "room": "R1", "speakers": [], "level": "300"},
        {"sessionId": "h2", "abbreviation": "BBB222", "title": "Second",
         "startTime": "2026-11-30T11:30:00", "endTime": "2026-11-30T12:30:00",
         "venue": "MGM Grand", "room": "R2", "speakers": [], "level": "300"},
    ]
    schedule = {"schedule": {
        "reserved": ["h1", "h2"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    meals = [e for e in week["timeline"] if e["kind"] == "meal"]
    assert [(m["meal"], m["when"]) for m in meals] == [
        ("breakfast", "morning, before 08:30"),
        ("lunch", "09:30–11:30"),
        ("dinner", "after 12:30"),
    ]
    assert meals[0]["place"] == "MGM Grand"
    assert "20-minute" in meals[0]["note"]
    assert meals[2]["place"] == "TBD"


def test_build_week_skips_lunch_outside_midday_window():
    catalog = [
        {"sessionId": "h1", "abbreviation": "AAA111", "title": "First",
         "startTime": "2026-11-30T15:00:00", "endTime": "2026-11-30T16:00:00",
         "venue": "MGM Grand", "room": "R1", "speakers": [], "level": "300"},
        {"sessionId": "h2", "abbreviation": "BBB222", "title": "Second",
         "startTime": "2026-11-30T17:00:00", "endTime": "2026-11-30T18:00:00",
         "venue": "MGM Grand", "room": "R2", "speakers": [], "level": "300"},
    ]
    schedule = {"schedule": {
        "reserved": ["h1", "h2"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    assert [e for e in week["timeline"] if e.get("meal") == "lunch"] == []


def test_build_week_early_close_is_brunch_not_dinner():
    catalog = [
        {"sessionId": "h1", "abbreviation": "AAA111", "title": "First",
         "startTime": "2026-12-04T08:00:00", "endTime": "2026-12-04T10:00:00",
         "venue": "Wynn/Encore", "room": "R1", "speakers": [], "level": "300"},
    ]
    schedule = {"schedule": {
        "reserved": ["h1"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    closing = [e for e in week["timeline"] if e["kind"] == "meal"
               and e.get("meal") != "breakfast"]
    assert [(c["meal"], c["when"]) for c in closing] == [("brunch", "after 10:00")]
    assert "re:Play" not in closing[0]["note"]


def test_build_week_thursday_dinner_names_replay():
    catalog = [
        {"sessionId": "h1", "abbreviation": "AAA111", "title": "First",
         "startTime": "2026-12-03T08:00:00", "endTime": "2026-12-03T17:30:00",
         "venue": "Wynn/Encore", "room": "R1", "speakers": [], "level": "300"},
    ]
    schedule = {"schedule": {
        "reserved": ["h1"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    dinner = [e for e in week["timeline"] if e.get("meal") == "dinner"]
    assert len(dinner) == 1
    assert "re:Play" in dinner[0]["note"]


def test_build_week_inserts_leg_between_venues():
    catalog = [
        {"sessionId": "h1", "abbreviation": "AAA111", "title": "First",
         "startTime": "2026-12-01T12:00:00", "endTime": "2026-12-01T13:00:00",
         "venue": "Wynn/Encore", "room": "R1", "speakers": [], "level": "300"},
        {"sessionId": "h2", "abbreviation": "BBB222", "title": "Second",
         "startTime": "2026-12-01T15:00:00", "endTime": "2026-12-01T16:00:00",
         "venue": "Caesars Forum", "room": "R2", "speakers": [], "level": "300"},
    ]
    schedule = {"schedule": {
        "reserved": ["h1", "h2"], "favorites": [], "personalTime": [],
    }}
    week = build_week(schedule, catalog, "/nonexistent", "2026-11-05")
    legs = [e for e in week["timeline"] if e["kind"] == "leg"]
    assert len(legs) == 1
    assert legs[0]["mode"] == "shuttle"
    assert "Caesars Forum" in legs[0]["to_venue"]
