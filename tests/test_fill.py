"""Gap-fit and priority rules for reinvent26 fill (no network)."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import fill  # noqa: E402

TEST_PLANNER_CONFIG = {
    "cluster_venues": ["Venetian", "Wynn/Encore", "Caesars Palace", "Caesars Forum"],
    "same_venue_gap": 0, "near_venue_gap": 30, "far_venue_gap": 60,
    "type_weight": {"Workshop": 30, "Chalk talk": 20, "Breakout session": 10, "_default": 5},
    "topics": [], "topic_weight": {},
    "bedrock_keywords": ["bedrock", "agentcore"], "frontier_title_patterns": ["frontier", "claude"],
}


def make_session(code, venue, start, end, type_="Chalk talk", title="t"):
    """Create a session dict with required fields for testing."""
    return {"abbreviation": code, "venue": venue, "type": type_, "title": title,
            "_start": datetime.fromisoformat(start), "_end": datetime.fromisoformat(end)}


def test_overlap_rejected():
    """Session overlapping held seat should be rejected."""
    held = [make_session("H", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    assert not fill.fits(make_session("C", "MGM Grand", "2026-11-30T10:30", "2026-11-30T11:30"), held, TEST_PLANNER_CONFIG)


def test_same_venue_back_to_back_fits():
    """Back-to-back sessions at same venue should fit with 0 min gap."""
    held = [make_session("H", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    assert fill.fits(make_session("C", "MGM Grand", "2026-11-30T11:00", "2026-11-30T12:00"), held, TEST_PLANNER_CONFIG)


def test_mgm_to_cluster_needs_an_hour():
    """Travel from MGM Grand to cluster venues requires 60 min gap."""
    held = [make_session("H", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    # 30 min gap insufficient (needs 60)
    assert not fill.fits(make_session("C", "Venetian", "2026-11-30T11:30", "2026-11-30T12:30"), held, TEST_PLANNER_CONFIG)
    # 60 min gap sufficient
    assert fill.fits(make_session("C", "Venetian", "2026-11-30T12:00", "2026-11-30T13:00"), held, TEST_PLANNER_CONFIG)


def test_gap_checked_before_a_held_seat():
    """Gap rule also checks if candidate ends before held starts."""
    held = [make_session("H", "MGM Grand", "2026-11-30T13:00", "2026-11-30T14:00")]
    # Candidate ends at 12:30, held starts at 13:00, but gap needed is 60 min
    assert not fill.fits(make_session("C", "Wynn/Encore", "2026-11-30T11:30", "2026-11-30T12:30"), held, TEST_PLANNER_CONFIG)


def test_other_days_ignored():
    """Gap rules only apply within the same day."""
    held = [make_session("H", "MGM Grand", "2026-12-01T10:00", "2026-12-01T11:00")]
    assert fill.fits(make_session("C", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00"), held, TEST_PLANNER_CONFIG)


def test_workshop_outranks_chalk_talk():
    """Higher format weight should produce higher priority."""
    workshop = make_session("W", "Venetian", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")
    chalk = make_session("C", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Chalk talk")
    breakout = make_session("B", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Breakout session")
    # Workshop (30) > Chalk talk (20) > Breakout (10) at equal duration
    assert fill.priority(workshop, TEST_PLANNER_CONFIG) > fill.priority(chalk, TEST_PLANNER_CONFIG) > fill.priority(breakout, TEST_PLANNER_CONFIG)


def make_session_with_id(code, session_id, venue, start, end, type_="Chalk talk"):
    """Create a session dict with sessionId for testing plan_days."""
    session = make_session(code, venue, start, end, type_)
    session["sessionId"] = session_id
    return session


def test_plan_days_prefers_more_sessions_then_minutes():
    """Plan prefers more sessions over longer single sessions (weighted interval scheduling)."""
    # two 1h chalk talks beat one 2h workshop covering the same window: as many events as possible
    pool = [make_session_with_id("C1", "c1", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("C2", "c2", "MGM Grand", "2026-11-30T11:00", "2026-11-30T12:00"),
            make_session_with_id("W", "w", "MGM Grand", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, set(), TEST_PLANNER_CONFIG)]
    assert got == ["C1", "C2"]


def test_plan_days_workshop_wins_same_window():
    """When sessions overlap, the one with higher weight wins."""
    pool = [make_session_with_id("C", "c", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("W", "w", "MGM Grand", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, set(), TEST_PLANNER_CONFIG)]
    assert got == ["W"]


def test_plan_days_keeps_held_on_tie():
    """Held seats get bonus (300) so they win ties in weighted interval scheduling."""
    pool = [make_session_with_id("A", "a", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("B", "b", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, {"b"}, TEST_PLANNER_CONFIG)]
    assert got == ["B"]


def test_plan_days_one_run_per_base():
    """Repeat sessions (-R variants) only scheduled once per base code."""
    pool = [make_session_with_id("X1-R", "x1", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("X1-R1", "x2", "MGM Grand", "2026-12-01T10:00", "2026-12-01T11:00")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, set(), TEST_PLANNER_CONFIG)]
    assert got == ["X1-R"]
