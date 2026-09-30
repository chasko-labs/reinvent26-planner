import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import rank  # noqa: E402


def test_parse_not_before_accept_query():
    floor = rank.parse_not_before("agents for a python dev, nothing before 9am")
    assert floor is not None and (floor.hour, floor.minute) == (9, 0)


def test_filter_not_before_drops_early():
    sessions = [
        {"sessionId": "early", "startTime": "2026-12-01T08:30:00"},
        {"sessionId": "late", "startTime": "2026-12-01T09:30:00"},
        {"sessionId": "timeless"},
    ]
    from datetime import time as _t
    out = rank.filter_not_before(sessions, _t(9, 0))
    ids = {s["sessionId"] for s in out}
    assert ids == {"late", "timeless"}


def test_parse_picks_validates_codes():
    sessions = [
        {"sessionId": "s1", "code": "AIM301", "title": "agents"},
        {"sessionId": "s2", "code": "STO201", "title": "storage"},
    ]
    raw = '{"picks": [{"code": "AIM301", "reason": "agents"}, '
    raw += '{"code": "NOPE999", "reason": "hallucinated"}, {"code": "AIM301"}]}'
    picks = rank.parse_picks(raw, sessions, top=10)
    assert [s["code"] for s in picks] == ["AIM301"]


def test_build_prompt_carries_query_and_codes():
    sessions = [{"sessionId": "s1", "code": "AIM301",
                 "title": "agents for python devs",
                 "level": "300", "topics": ["agents"],
                 "startTime": "2026-12-01T10:00:00"}]
    system, user = rank.build_prompt(
        "agents for a python dev, nothing before 9am", sessions, 5)
    assert "AIM301" in user and "python dev" in user
    assert "EVENTS_ACCESS_TOKEN" not in system + user
