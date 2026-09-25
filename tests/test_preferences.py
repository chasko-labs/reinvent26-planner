import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

import pytest  # noqa: E402

from reinvent26.schedule import filter_by_time, find_offbeat  # noqa: E402

EARLY = {"sessionId": "early", "title": "agents at dawn", "topics": ["agents"],
         "startTime": "2026-12-01T08:00:00", "endTime": "2026-12-01T09:00:00"}
MID = {"sessionId": "mid", "title": "agents at noon", "topics": ["agents"],
       "startTime": "2026-12-01T12:30:00", "endTime": "2026-12-01T13:30:00"}
LATE = {"sessionId": "late", "title": "quantum at dusk", "topics": ["quantum"],
        "startTime": "2026-12-01T18:00:00", "endTime": "2026-12-01T19:00:00"}
TIMELESS = {"sessionId": "tbd", "title": "agents session tbd"}


def test_not_before_drops_early_sessions():
    out = filter_by_time([EARLY, MID, LATE], not_before="09:00")
    assert [s["sessionId"] for s in out] == ["mid", "late"]


def test_not_after_drops_late_sessions():
    out = filter_by_time([EARLY, MID, LATE], not_after="17:00")
    assert [s["sessionId"] for s in out] == ["early", "mid"]


def test_lunch_blocks_overlapping_session():
    out = filter_by_time([EARLY, MID, LATE], lunch="12:00-13:00")
    assert [s["sessionId"] for s in out] == ["early", "late"]


def test_timeless_sessions_are_kept():
    out = filter_by_time([TIMELESS, EARLY], not_before="09:00", lunch="07:00-08:30")
    assert [s["sessionId"] for s in out] == ["tbd"]


def test_bad_time_format_raises():
    with pytest.raises(ValueError):
        filter_by_time([EARLY], not_before="9am")
    with pytest.raises(ValueError):
        filter_by_time([EARLY], lunch="12:00")


def test_offbeat_returns_exactly_one_outsider():
    pick = find_offbeat([EARLY, MID, LATE], ["agents"])
    assert pick is not None and pick["sessionId"] == "late"


def test_offbeat_none_when_everything_matches():
    assert find_offbeat([EARLY, MID], ["agents"]) is None
