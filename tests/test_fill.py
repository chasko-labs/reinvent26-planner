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
    held = [make_session("HELD", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    assert not fill.fits(make_session("CANDIDATE", "MGM Grand", "2026-11-30T10:30", "2026-11-30T11:30"), held, TEST_PLANNER_CONFIG)


def test_same_venue_back_to_back_fits():
    """Back-to-back sessions at same venue should fit with 0 min gap."""
    held = [make_session("HELD", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    assert fill.fits(make_session("CANDIDATE", "MGM Grand", "2026-11-30T11:00", "2026-11-30T12:00"), held, TEST_PLANNER_CONFIG)


def test_mgm_to_cluster_needs_an_hour():
    """Travel from MGM Grand to cluster venues requires 60 min gap."""
    held = [make_session("HELD", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    # 30 min gap insufficient (needs 60)
    assert not fill.fits(make_session("CANDIDATE", "Venetian", "2026-11-30T11:30", "2026-11-30T12:30"), held, TEST_PLANNER_CONFIG)
    # 60 min gap sufficient
    assert fill.fits(make_session("CANDIDATE", "Venetian", "2026-11-30T12:00", "2026-11-30T13:00"), held, TEST_PLANNER_CONFIG)


def test_gap_checked_before_a_held_seat():
    """Gap rule also checks if candidate ends before held starts."""
    held = [make_session("HELD", "MGM Grand", "2026-11-30T13:00", "2026-11-30T14:00")]
    # Candidate ends at 12:30, held starts at 13:00, but gap needed is 60 min
    assert not fill.fits(make_session("CANDIDATE", "Wynn/Encore", "2026-11-30T11:30", "2026-11-30T12:30"), held, TEST_PLANNER_CONFIG)


def test_other_days_ignored():
    """Gap rules only apply within the same day."""
    held = [make_session("HELD", "MGM Grand", "2026-12-01T10:00", "2026-12-01T11:00")]
    assert fill.fits(make_session("CANDIDATE", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00"), held, TEST_PLANNER_CONFIG)


def test_workshop_outranks_chalk_talk():
    """Higher format weight should produce higher priority."""
    workshop = make_session("WORKSHOP", "Venetian", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")
    chalk = make_session("CHALK", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Chalk talk")
    breakout = make_session("BREAKOUT", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Breakout session")
    # Workshop (30) > Chalk talk (20) > Breakout (10) at equal duration
    assert fill.priority(workshop, TEST_PLANNER_CONFIG) > fill.priority(chalk, TEST_PLANNER_CONFIG) > fill.priority(breakout, TEST_PLANNER_CONFIG)


def test_scarcest_seat_books_first():
    """veryLimited outranks available even when format priority says otherwise."""
    open_workshop = make_session_with_id("OPEN-WRK", "open-workshop", "Venetian", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")
    scarce_chalk = make_session_with_id("SCARCE-CHK", "scarce-chalk", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Chalk talk")
    seats = {"open-workshop": "available", "scarce-chalk": "veryLimited"}
    ordered = [s["sessionId"] for s in fill.booking_order([open_workshop, scarce_chalk], seats, TEST_PLANNER_CONFIG)]
    assert ordered == ["scarce-chalk", "open-workshop"]


def test_booking_order_breaks_scarcity_ties_by_priority():
    """Same seat band falls back to format priority."""
    limited_chalk = make_session_with_id("LTD-CHK", "limited-chalk", "Venetian", "2026-11-30T10:00", "2026-11-30T11:00", "Chalk talk")
    limited_workshop = make_session_with_id("LTD-WRK", "limited-workshop", "Venetian", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")
    seats = {"limited-chalk": "limited", "limited-workshop": "limited"}
    ordered = [s["sessionId"] for s in fill.booking_order([limited_chalk, limited_workshop], seats, TEST_PLANNER_CONFIG)]
    assert ordered == ["limited-workshop", "limited-chalk"]


def test_reason_names_seat_format_and_topics():
    """Reason line carries the seat band, format, and topic match."""
    config = dict(TEST_PLANNER_CONFIG, topics=[{"name": "agents", "pattern": "agent"}])
    session = make_session_with_id("AGENT-WRK", "agent-workshop", "Venetian", "2026-12-01T15:00", "2026-12-01T16:00", "Workshop")
    session["title"] = "agent session"
    text = fill.reason(session, "veryLimited", config)
    assert "veryLimited" in text and "Workshop" in text and "agents" in text


def make_session_with_id(code, session_id, venue, start, end, type_="Chalk talk"):
    """Create a session dict with sessionId for testing plan_days."""
    session = make_session(code, venue, start, end, type_)
    session["sessionId"] = session_id
    return session


def test_plan_days_prefers_more_sessions_then_minutes():
    """Plan prefers more sessions over longer single sessions (weighted interval scheduling)."""
    # two 1h chalk talks beat one 2h workshop covering the same window: as many events as possible
    pool = [make_session_with_id("CHALK-ONE", "chalk-one", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("CHALK-TWO", "chalk-two", "MGM Grand", "2026-11-30T11:00", "2026-11-30T12:00"),
            make_session_with_id("WORKSHOP", "workshop", "MGM Grand", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, set(), TEST_PLANNER_CONFIG)]
    assert got == ["CHALK-ONE", "CHALK-TWO"]


def test_plan_days_workshop_wins_same_window():
    """When sessions overlap, the one with higher weight wins."""
    pool = [make_session_with_id("CHALK", "chalk", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("WORKSHOP", "workshop", "MGM Grand", "2026-11-30T10:00", "2026-11-30T12:00", "Workshop")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, set(), TEST_PLANNER_CONFIG)]
    assert got == ["WORKSHOP"]


def test_plan_days_keeps_held_on_tie():
    """Held seats get bonus (300) so they win ties in weighted interval scheduling."""
    pool = [make_session_with_id("FIRST", "first", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("SECOND", "second", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, {"second"}, TEST_PLANNER_CONFIG)]
    assert got == ["SECOND"]


def test_plan_days_one_run_per_base():
    """Repeat sessions (-R variants) only scheduled once per base code."""
    pool = [make_session_with_id("X1-R", "repeat-first", "MGM Grand", "2026-11-30T10:00", "2026-11-30T11:00"),
            make_session_with_id("X1-R1", "repeat-second", "MGM Grand", "2026-12-01T10:00", "2026-12-01T11:00")]
    got = [s["abbreviation"] for s in fill.plan_days(pool, set(), TEST_PLANNER_CONFIG)]
    assert got == ["X1-R"]


def test_resolve_catalog_path_prefers_catalog_json(tmp_path, monkeypatch):
    """catalog.json wins when both cached pulls exist."""
    cache_dir = tmp_path / ".cache" / "reinvent2026"
    cache_dir.mkdir(parents=True)
    (cache_dir / "catalog.json").write_text("[]")
    (cache_dir / "sessions.json").write_text("[]")
    monkeypatch.setattr(fill, "repo_root", lambda: str(tmp_path))
    assert fill.resolve_catalog_path() == str(cache_dir / "catalog.json")


def test_resolve_catalog_path_falls_back_to_sessions_json(tmp_path, monkeypatch):
    """sessions.json resolves when catalog.json is absent."""
    cache_dir = tmp_path / ".cache" / "reinvent2026"
    cache_dir.mkdir(parents=True)
    (cache_dir / "sessions.json").write_text("[]")
    monkeypatch.setattr(fill, "repo_root", lambda: str(tmp_path))
    assert fill.resolve_catalog_path() == str(cache_dir / "sessions.json")


def test_resolve_catalog_path_missing_reports_pull(tmp_path, monkeypatch, capsys):
    """Neither file resolves to None with the pull command named."""
    cache_dir = tmp_path / ".cache" / "reinvent2026"
    cache_dir.mkdir(parents=True)
    monkeypatch.setattr(fill, "repo_root", lambda: str(tmp_path))
    assert fill.resolve_catalog_path() is None
    assert "sessions reinvent2026 --refresh" in capsys.readouterr().err
