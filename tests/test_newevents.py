"""Unit tests for the daily new-session watcher (network-free)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import newevents as ne  # noqa: E402


def _s(sid, **kw):
    row = {"sessionId": sid, "code": sid.upper(), "title": f"title {sid}"}
    row.update(kw)
    return row


def test_diff_finds_added_and_removed():
    old = [_s("sess-kept"), _s("sess-gone"), {"no-id": True}]
    live = [_s("sess-kept"), _s("sess-added"), {"no-id": True}]
    added, removed = ne.diff_catalogs(old, live)
    assert [s["sessionId"] for s in added] == ["sess-added"]
    assert [s["sessionId"] for s in removed] == ["sess-gone"]


def test_diff_empty_old_treats_all_live_as_added():
    added, removed = ne.diff_catalogs([], [_s("sess-first")])
    assert [s["sessionId"] for s in added] == ["sess-first"]
    assert removed == []


def test_parse_session_detail_wrapped_and_flat():
    wrapped = {"session": {"seatAvailability": "limited", "abstract": "abc", "isReservable": True}}
    assert ne.parse_session_detail(wrapped) == ("limited", "abc", True)
    flat = {"seatAvailability": "available", "description": "d", "isReservable": False}
    assert ne.parse_session_detail(flat) == ("available", "d", False)
    assert ne.parse_session_detail({}) == (None, "", None)
    assert ne.parse_session_detail(None) == (None, "", None)


def test_evaluate_orders_core_first():
    config = {"topics": [{"name": "agents", "pattern": "agent"}]}
    tagged = _s("sess-agent-talk", title="agent session")
    plain = _s("sess-storage-talk", title="storage deep dive")
    ranked = ne.evaluate([plain, tagged], config)
    assert [s["sessionId"] for s in ranked] == ["sess-agent-talk", "sess-storage-talk"]
    assert ranked[0]["_core"] == ["agents"]


def test_opportunities_splits_fits_and_conflicts():
    from reinvent26 import mapper
    config = mapper._load_config()
    held = [_s("sess-held-noon", startTime="2026-12-01T12:00:00", endTime="2026-12-01T13:00:00",
                venue="Wynn/Encore", type="Chalk talk")]
    free = _s("sess-fitting-open", startTime="2026-12-01T15:00:00", endTime="2026-12-01T16:00:00",
              venue="Wynn/Encore", type="Chalk talk", _seat="available")
    clash = _s("sess-clashing-open", startTime="2026-12-01T12:30:00", endTime="2026-12-01T13:30:00",
               venue="Wynn/Encore", type="Chalk talk", _seat="limited")
    full = _s("sess-fitting-full", startTime="2026-12-01T15:00:00", endTime="2026-12-01T16:00:00",
              venue="Wynn/Encore", type="Chalk talk", _seat="unavailable")
    fits, conflicts = ne.opportunities([free, clash, full], held, config)
    assert [s["sessionId"] for s in fits] == ["sess-fitting-open"]
    assert [s["sessionId"] for s, _ in conflicts] == ["sess-clashing-open"]


def test_render_report_has_all_sections_and_handoff():
    fits = [_s("sess-fit-talk", startTime="2026-12-01T15:00:00", endTime="2026-12-01T16:00:00",
                venue="Wynn/Encore", type="Chalk talk", level="300",
                title="fit talk", _seat="available", _core=["agents"])]
    report = ne.render_report("2026-11-05", "reinvent2026", fits, [], fits, [],
                              [], 14, "topic-tags")
    for section in ("opportunities", "launch signals", "conflicts", "unchecked",
                    "removed", "all added sessions", "handoff to kiro-cli"):
        assert section in report
    assert "fit talk" in report


def test_render_report_lists_launch_signals():
    sig = {"code": "NEW-LAUNCH", "sessionId": "sess-new", "title": "Introducing Foo",
           "_sig": "title", "_kw": "introduc"}
    report = ne.render_report("2026-11-05", "reinvent2026", [], [], [], [],
                              [], 0, "topic-tags", [sig])
    assert "launch signals among new sessions" in report
    assert "NEW-LAUNCH" in report and "[title]" in report
    empty = ne.render_report("2026-11-05", "reinvent2026", [], [], [], [],
                             [], 0, "topic-tags", [])
    assert "no added session title or abstract signals a launch" in empty


def test_render_handoff_names_ids_and_conflicts():
    fits = [_s("sess-fit", sessionId="sess-fit")]
    conflicts = [(_s("sess-clash", sessionId="sess-clash"), [_s("sess-held")])]
    text = ne.render_handoff("reinvent2026", fits, conflicts)
    assert "sess-fit" in text and "sess-clash" in text
    assert "GetSchedule" in text
    assert "Reserve nothing new" in ne.render_handoff("reinvent2026", [], [])
