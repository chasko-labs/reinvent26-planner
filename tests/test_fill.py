"""Gap-fit and priority rules for reinvent26 fill (no network)."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import fill  # noqa: E402

CONFIG = {
    "cluster_venues": ["Venetian", "Wynn/Encore", "Caesars Palace", "Caesars Forum"],
    "same_venue_gap": 0, "near_venue_gap": 30, "far_venue_gap": 60,
    "type_weight": {"Workshop": 30, "Chalk talk": 20, "Breakout session": 10, "_default": 5},
    "topics": [], "topic_weight": {},
    "bedrock_keywords": ["bedrock", "agentcore"], "frontier_title_patterns": ["frontier", "claude"],
}


def _s(code, venue, start, end, type_="Chalk talk", title="t"):
    return {"abbreviation": code, "venue": venue, "type": type_, "title": title,
            "_start": datetime.fromisoformat(start), "_end": datetime.fromisoformat(end)}


def test_overlap_rejected():
    held = [_s("H", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    assert not fill.fits(_s("C", "MGM Grand", "2026-11-30T10:30", "2026-11-30T11:30"), held, CONFIG)


def test_same_venue_back_to_back_fits():
    held = [_s("H", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    assert fill.fits(_s("C", "MGM Grand", "2026-11-30T11:00", "2026-11-30T12:00"), held, CONFIG)


def test_mgm_to_cluster_needs_an_hour():
    held = [_s("H", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    assert not fill.fits(_s("C", "Venetian", "2026-11-30T11:30", "2026-11-30T12:30"), held, CONFIG)
    assert fill.fits(_s("C", "Venetian", "2026-11-30T12:00", "2026-11-30T13:00"), held, CONFIG)


def test_gap_checked_before_a_held_seat():
    held = [_s("H", "MGM Grand", "2026-11-30T13:00", "2026-11-30T14:00")]
    assert not fill.fits(_s("C", "Wynn/Encore", "2026-11-30T11:30", "2026-11-30T12:30"), held, CONFIG)


def test_other_days_ignored():
    held = [_s("H", "MGM Grand", "2026-12-01T10:00", "2026-12-01T11:00")]
    assert fill.fits(_s("C", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00"), held, CONFIG)


def test_workshop_outranks_chalk_talk():
    w = _s("W", "Venetian", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")
    c = _s("C", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Chalk talk")
    b = _s("B", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Breakout session")
    assert fill.priority(w, CONFIG) > fill.priority(c, CONFIG) > fill.priority(b, CONFIG)
