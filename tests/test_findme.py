"""Unit tests for the find-me page (no network)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import findme  # noqa: E402


def _held(start, end, code="HELD"):
    return {"sessionId": code, "abbreviation": code, "venue": "MGM Grand",
            "title": f"title {code}", "startTime": start, "endTime": end}


def test_day_gaps_skips_short_windows():
    held = [_held("2026-12-01T08:00:00", "2026-12-01T10:00:00", "morning-one"),
            _held("2026-12-01T10:30:00", "2026-12-01T11:30:00", "midday-two"),
            _held("2026-12-01T15:00:00", "2026-12-01T16:00:00", "evening-three")]
    gaps = findme.day_gaps(held)
    assert len(gaps) == 1
    day, start, end, minutes, part = gaps[0]
    assert (minutes, part) == (210, "morning")


def test_day_gaps_labels_morning_and_evening():
    held = [_held("2026-12-01T08:00:00", "2026-12-01T09:00:00", "early-one"),
            _held("2026-12-01T10:30:00", "2026-12-01T11:30:00", "early-two"),
            _held("2026-12-01T18:00:00", "2026-12-01T19:00:00", "late-three"),
            _held("2026-12-01T20:30:00", "2026-12-01T21:30:00", "late-four")]
    parts = [g[4] for g in findme.day_gaps(held)]
    assert parts == ["morning", "morning", "evening"]


def test_day_gaps_ignores_timeless_entries():
    assert findme.day_gaps([{"abbreviation": "BARE"}]) == []


def test_visitor_prompt_picks_question_by_day():
    assert "most excited to see" in findme.visitor_prompt(1)
    assert "most excited to see" in findme.visitor_prompt(None)
    assert "best thing you have seen so far" in findme.visitor_prompt(3)
    assert "best thing you have seen so far" in findme.visitor_prompt(5)
    assert "architecture or topic" in findme.visitor_prompt(2)


def test_talk_topics_orders_most_held_first():
    config = {"topics": [{"name": "agents", "pattern": "agent"},
                         {"name": "leo", "pattern": "leo"}]}
    items = [{"title": "agent one"}, {"title": "agent two"}, {"title": "leo chat"}]
    assert findme.talk_topics(items, config) == ["agents", "leo"]


def test_render_findme_has_all_sections():
    held = [_held("2026-12-01T08:00:00", "2026-12-01T10:00:00", "MORNING-KEYNOTE")]
    gaps = findme.day_gaps(held + [_held("2026-12-01T12:00:00", "2026-12-01T13:00:00", "MIDDAY-TALK")])
    text = findme.render_findme("2026-11-04", held, gaps, ["agents"], 1)
    assert "MORNING-KEYNOTE" in text
    assert "midday" in text
    assert "agents" in text
    assert "most excited to see" in text
