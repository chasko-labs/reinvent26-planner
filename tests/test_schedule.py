import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26.schedule import (  # noqa: E402
    find_clashes,
    find_open_slots,
    match_topics,
    stack_keywords,
)


def test_no_clash_when_sequential():
    items = [
        {"sessionId": "a", "startTime": "2026-12-01T09:00:00", "endTime": "2026-12-01T10:00:00"},
        {"sessionId": "b", "startTime": "2026-12-01T10:00:00", "endTime": "2026-12-01T11:00:00"},
    ]
    assert find_clashes(items) == []


def test_clash_when_overlap():
    items = [
        {"sessionId": "a", "startTime": "2026-12-01T09:00:00", "endTime": "2026-12-01T10:00:00"},
        {"sessionId": "b", "startTime": "2026-12-01T09:30:00", "endTime": "2026-12-01T10:30:00"},
    ]
    clashes = find_clashes(items)
    assert len(clashes) == 1


def test_open_slot_finder_skips_clash():
    sessions = [
        {"sessionId": "a", "startTime": "2026-12-01T09:00:00", "endTime": "2026-12-01T10:00:00"},
        {"sessionId": "b", "startTime": "2026-12-01T14:00:00", "endTime": "2026-12-01T15:00:00"},
    ]
    windows = [{"start": "2026-12-01T13:00:00", "end": "2026-12-01T16:00:00"}]
    out = find_open_slots(sessions, windows)
    assert [s["sessionId"] for s in out] == ["b"]


def test_match_topics_ranks_and_excludes():
    sessions = [
        {"sessionId": "a", "title": "agents with bedrock", "topics": ["agents"]},
        {"sessionId": "b", "title": "s3 deep dive", "topics": ["storage"]},
    ]
    ranked = match_topics(sessions, ["agents", "bedrock"])
    assert ranked[0]["sessionId"] == "a"
    ranked2 = match_topics(sessions, ["agents", "s3"], exclude=["bedrock"])
    assert all("bedrock" not in (s.get("title", "")) for s in ranked2)


def test_stack_keywords_maps_lambda():
    kws = stack_keywords([{"service": "AWS::Lambda::Function"}])
    assert "lambda" in kws


def test_clash_finds_non_adjacent_overlap():
    items = [
        {"sessionId": "long", "startTime": "2026-12-01T10:00:00", "endTime": "2026-12-01T13:00:00"},
        {"sessionId": "early", "startTime": "2026-12-01T11:00:00", "endTime": "2026-12-01T12:00:00"},
        {"sessionId": "late", "startTime": "2026-12-01T12:30:00", "endTime": "2026-12-01T14:00:00"},
    ]
    clashes = find_clashes(items)
    pairs = {(a["sessionId"], b["sessionId"]) for a, b in clashes}
    assert ("long", "early") in pairs
    assert ("long", "late") in pairs


def test_open_slots_ignores_preexisting_scheduled_clashes():
    scheduled = [
        {"sessionId": "held", "startTime": "2026-12-01T13:00:00", "endTime": "2026-12-01T14:00:00"},
        {"sessionId": "fav", "startTime": "2026-12-01T13:30:00", "endTime": "2026-12-01T14:30:00"},
    ]
    sessions = [
        {"sessionId": "free", "startTime": "2026-12-01T14:30:00", "endTime": "2026-12-01T15:30:00"},
        {"sessionId": "busy", "startTime": "2026-12-01T13:00:00", "endTime": "2026-12-01T13:30:00"},
    ]
    windows = [{"start": "2026-12-01T13:00:00", "end": "2026-12-01T16:00:00"}]
    out = find_open_slots(sessions, windows, scheduled)
    assert [s["sessionId"] for s in out] == ["free"]


def test_open_slots_empty_scheduled_still_filters_candidate_clash():
    scheduled = [
        {"sessionId": "held", "startTime": "2026-12-01T13:00:00", "endTime": "2026-12-01T14:00:00"},
    ]
    sessions = [
        {"sessionId": "busy", "startTime": "2026-12-01T13:30:00", "endTime": "2026-12-01T14:30:00"},
    ]
    windows = [{"start": "2026-12-01T13:00:00", "end": "2026-12-01T16:00:00"}]
    assert find_open_slots(sessions, windows, scheduled) == []
