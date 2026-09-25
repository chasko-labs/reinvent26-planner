import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

import pytest  # noqa: E402

from reinvent26.cli import _parse_window, _schedule_items, build_parser  # noqa: E402


def test_parse_window_ok():
    w = _parse_window("2026-12-01T13:00:00,2026-12-01T16:00:00")
    assert w == {"start": "2026-12-01T13:00:00", "end": "2026-12-01T16:00:00"}


def test_parse_window_rejects_bad_shapes():
    with pytest.raises(ValueError):
        _parse_window("2026-12-01T13:00:00")
    with pytest.raises(ValueError):
        _parse_window("2026-12-01T16:00:00,2026-12-01T13:00:00")
    with pytest.raises(ValueError):
        _parse_window("not-a-time,also-not-a-time")


def test_schedule_items_accepts_all_shapes():
    assert _schedule_items({"items": [1]}) == [1]
    assert _schedule_items({"sessions": [2]}) == [2]
    assert _schedule_items({"schedule": [3]}) == [3]
    assert _schedule_items([4]) == [4]
    assert _schedule_items({}) == []


def test_confirmed_items_resolves_live_shape():
    from reinvent26.cli import _confirmed_items
    catalog = [{"sessionId": "s1", "code": "A1", "title": "agents talk",
                "startTime": "2026-12-01T10:00:00",
                "endTime": "2026-12-01T11:00:00"}]
    sched = {"schedule": {"favorites": ["s1", "unknown-9"],
                          "reserved": [],
                          "personalTime": [{"title": "Lunch"}]}}
    items = _confirmed_items(sched, catalog)
    assert items[0]["code"] == "A1"
    assert items[1] == {"sessionId": "unknown-9"}
    assert items[2] == {"title": "Lunch"}


def test_slots_parser_requires_window():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["slots", "evt"])
    args = build_parser().parse_args(
        ["slots", "evt", "--window", "2026-12-01T13:00:00,2026-12-01T16:00:00"]
    )
    assert args.window == ["2026-12-01T13:00:00,2026-12-01T16:00:00"]


def test_normalize_live_shape():
    from reinvent26.schedule import normalize_session
    live = {"sessionId": "x", "abbreviation": "ANT301", "title": "t",
            "sessionTime": {"date": "2026-12-01", "length": "90",
                            "time": "10:30"}}
    out = normalize_session(live)
    assert out["code"] == "ANT301"
    assert out["startTime"] == "2026-12-01T10:30:00"
    assert out["endTime"] == "2026-12-01T12:00:00"
    assert out["title"] == "t" and out["sessionTime"]["length"] == "90"


def test_normalize_timeless_and_idempotent():
    from reinvent26.schedule import normalize_session
    assert normalize_session({"sessionId": "x"}) == {"sessionId": "x"}
    bad = {"sessionId": "y",
           "sessionTime": {"date": "nope", "length": "60", "time": "10:30"}}
    assert "startTime" not in normalize_session(bad)
    canon = {"sessionId": "z", "code": "A1",
             "startTime": "2026-12-01T10:00:00",
             "endTime": "2026-12-01T11:00:00"}
    assert normalize_session(canon) == canon
