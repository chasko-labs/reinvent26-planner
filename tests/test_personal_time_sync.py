import io
import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import api  # noqa: E402
from reinvent26 import cli as cli_mod  # noqa: E402
from reinvent26 import personal_time as pt  # noqa: E402
from reinvent26.schedule import validate_personal_time  # noqa: E402

WEEK = {
    "event_id": "reinvent2026",
    "timeline": [
        {"kind": "meal", "meal": "breakfast", "date": "2026-11-30",
         "start": "", "end": "08:20", "place": "MGM Grand",
         "note": "breakfast near MGM Grand " + "x" * 300},
        {"kind": "held", "code": "STG363", "date": "2026-11-30",
         "start": "08:30", "end": "09:30", "venue": "MGM Grand",
         "room": "Level 3 | Room 306"},
        {"kind": "leg", "date": "2026-11-30", "start": "09:32",
         "end": "09:32", "from_venue": "MGM Grand", "to_venue": "Wynn/Encore",
         "from_room": "Level 3 | Room 306", "to_room": "Level 1 | Chopin 4",
         "mode": "shuttle", "label": "shuttle, about 43 minutes (estimate)"},
        {"kind": "open", "date": "2026-11-30", "start": "10:20",
         "end": "11:30", "minutes": 70, "part": "morning"},
        {"kind": "meal", "meal": "dinner", "date": "2026-11-30",
         "start": "23:00", "end": "", "place": "TBD", "note": "late dinner"},
    ],
}


class FakeApi:
    """Mocked http layer: an in-memory personal-time store."""

    def __init__(self, live=None):
        self.live = [dict(p) for p in (live or [])]
        self.calls = []
        self.n = 0

    def __call__(self, method, path, token=None, params=None, body=None, **_):
        self.calls.append((method, path, body))
        if method == "GET" and path.endswith("/schedule"):
            return {"schedule": {"reserved": [], "favorites": [],
                                 "personalTime": [dict(p) for p in self.live]}}
        if method == "POST" and path.endswith("/personal-time"):
            self.n += 1
            self.live.append({"personalTimeId": f"pt-{self.n}",
                              "title": body["title"],
                              "description": body["description"],
                              "location": body.get("location"),
                              "startDateTime": body["startDateTime"],
                              "endDateTime": body["endDateTime"]})
            return {}
        pid = path.rsplit("/", 1)[-1]
        if method == "PUT":
            for p in self.live:
                if p["personalTimeId"] == pid:
                    p.update(title=body["title"], description=body["description"],
                             location=body["location"],
                             startDateTime=body["startDateTime"],
                             endDateTime=body["endDateTime"])
            return {}
        if method == "DELETE":
            self.live = [p for p in self.live if p["personalTimeId"] != pid]
            return {}
        raise AssertionError((method, path))

    def ops(self):
        return [m for m, _, _ in self.calls if m != "GET"]


# rounding


def test_floor_and_ceil_to_five():
    assert pt.floor5(572) == 570
    assert pt.floor5(570) == 570
    assert pt.ceil5(572) == 575
    assert pt.ceil5(575) == 575


def test_entries_round_and_derive_spans():
    entries, skipped = pt.build_entries(WEEK)
    by_title = {e["title"]: e for e in entries}
    bf = by_title["Breakfast near MGM Grand"]
    assert (bf["start"], bf["end"]) == ("2026-11-30T07:50:00",
                                       "2026-11-30T08:20:00")
    leg = by_title["Shuttle to Wynn/Encore"]
    # 09:32 floors to 09:30; 09:32 + 43 = 10:15 already on the grid
    assert (leg["start"], leg["end"]) == ("2026-11-30T09:30:00",
                                         "2026-11-30T10:15:00")
    assert leg["location"] == "Wynn/Encore, Level 1, Chopin 4"
    win = by_title["Open window: find Bryan"]
    assert win["location"] == "Wynn/Encore, Level 1, Chopin 4"
    for e in entries:
        assert "|" not in e["title"] + e["description"] + (e["location"] or "")
        validate_personal_time(e["title"], e["start"], e["end"],
                               description=e["description"],
                               location=e["location"])


def test_description_trimmed_to_250():
    entries, _ = pt.build_entries(WEEK)
    bf = next(e for e in entries if e["title"].startswith("Breakfast"))
    assert len(bf["description"]) == 250


def test_crossing_midnight_is_skipped_and_reported():
    entries, skipped = pt.build_entries(WEEK)
    assert [s["reason"] for s in skipped] == ["crosses midnight"]
    assert skipped[0]["title"] == "Dinner (place TBD)"
    assert not any(e["title"].startswith("Dinner") for e in entries)


# field validation


def test_validation_rules_from_the_guide():
    ok = ("2026-12-01T12:00:00", "2026-12-01T13:00:00")
    validate_personal_time("Lunch", *ok, description="d", location="x" * 255)
    with pytest.raises(ValueError, match="same date"):
        validate_personal_time("Lunch", "2026-12-01T23:00:00",
                               "2026-12-02T00:30:00")
    with pytest.raises(ValueError, match="description"):
        validate_personal_time("Lunch", *ok, description="")
    with pytest.raises(ValueError, match="description"):
        validate_personal_time("Lunch", *ok, description="x" * 251)
    with pytest.raises(ValueError, match="location"):
        validate_personal_time("Lunch", *ok, location="x" * 256)
    with pytest.raises(ValueError):
        validate_personal_time("Lunch", "2026-12-01T12:00:00+01:00", ok[1])
    with pytest.raises(ValueError, match="5-minute"):
        validate_personal_time("Lunch", ok[0], "2026-12-01T12:03:00")


def test_create_sends_the_documented_body(monkeypatch):
    fake = FakeApi()
    monkeypatch.setattr(api, "_request", fake)
    api.create_personal_time("evt", "tok", "Lunch", "2026-12-01T12:00:00",
                             "2026-12-01T12:45:00", description="d",
                             location="MGM Grand")
    method, path, body = fake.calls[0]
    assert (method, path) == ("POST", "/v1/events/evt/personal-time")
    assert body == {"title": "Lunch", "description": "d",
                    "startDateTime": "2026-12-01T12:00:00",
                    "endDateTime": "2026-12-01T12:45:00",
                    "location": "MGM Grand"}


# idempotent matching


def test_first_apply_creates_then_second_run_is_all_noop(monkeypatch):
    fake = FakeApi()
    monkeypatch.setattr(api, "_request", fake)
    entries, _ = pt.build_entries(WEEK)
    actions = pt.plan(entries, [], {})
    assert {a["op"] for a in actions} == {"create"}
    state, failures = pt.apply("evt", "tok", actions, {})
    assert failures == []
    assert sorted(state.values()) == ["pt-1", "pt-2", "pt-3"]

    live = pt.schedule_personal_time(api.get_schedule("evt", "tok"))
    again = pt.plan(entries, live, state)
    assert {a["op"] for a in again} == {"noop"}
    assert pt.verify(entries, live) == []


def test_lost_state_matches_by_title_and_start_and_updates(monkeypatch):
    entries, _ = pt.build_entries(WEEK)
    leg = next(e for e in entries if e["title"].startswith("Shuttle"))
    live = [{"personalTimeId": "pt-old", "title": leg["title"],
             "description": "stale", "startDateTime": leg["start"],
             "endDateTime": leg["end"]}]
    actions = pt.plan(entries, live, {})
    hit = next(a for a in actions if a["entry"]["key"] == leg["key"])
    assert hit == {"op": "update", "entry": leg, "id": "pt-old"}
    assert sum(a["op"] == "create" for a in actions) == len(entries) - 1


def test_duplicates_deleted_and_hand_made_blocks_left_alone():
    entries, _ = pt.build_entries(WEEK)
    win = next(e for e in entries if e["title"].startswith("Open"))
    twin = {"title": win["title"], "description": win["description"],
            "location": win["location"], "startDateTime": win["start"],
            "endDateTime": win["end"]}
    live = [dict(twin, personalTimeId="a"), dict(twin, personalTimeId="b"),
            {"personalTimeId": "mine", "title": "Gym",
             "description": "gym", "startDateTime": "2026-11-30T06:00:00",
             "endDateTime": "2026-11-30T07:00:00"}]
    actions = pt.plan(entries, live, {})
    ops = {(a["op"], a["id"]) for a in actions if a["id"]}
    assert ("noop", "a") in ops
    assert ("delete", "b") in ops
    assert not any(a["id"] == "mine" for a in actions)


def test_apply_400_on_one_entry_continues_and_keeps_others(monkeypatch):
    fake = FakeApi()

    def flaky(method, path, token=None, params=None, body=None, **kw):
        if method == "POST" and body["title"].startswith("Shuttle"):
            raise api.EventsError(400, "could not be applied")
        return fake(method, path, token=token, params=params, body=body)

    monkeypatch.setattr(api, "_request", flaky)
    entries, _ = pt.build_entries(WEEK)
    state, failures = pt.apply("evt", "tok", pt.plan(entries, [], {}), {})
    assert [f["entry"]["title"] for f in failures] == ["Shuttle to Wynn/Encore"]
    assert len(state) == 2 and len(fake.live) == 2


def test_omitted_location_stored_as_personal_is_unchanged():
    entries = [{"key": "k", "title": "Dinner (place TBD)", "description": "d",
                "location": None, "start": "2026-11-30T17:00:00",
                "end": "2026-11-30T18:30:00"}]
    live = [{"personalTimeId": "x", "title": "Dinner (place TBD)",
             "description": "d", "location": "Personal",
             "startDateTime": "2026-11-30T17:00:00",
             "endDateTime": "2026-11-30T18:30:00"}]
    assert pt.plan(entries, live, {"k": "x"})[0]["op"] == "noop"


def test_dropped_entry_in_state_is_deleted():
    entries, _ = pt.build_entries(WEEK)
    live = [{"personalTimeId": "gone", "title": "Lunch near X",
             "description": "d", "startDateTime": "2026-11-29T12:00:00",
             "endDateTime": "2026-11-29T12:30:00"}]
    actions = pt.plan(entries, live, {"2026-11-29:meal:lunch:1": "gone"})
    assert ("delete", "gone") in {(a["op"], a["id"]) for a in actions}


# cli


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        try:
            cli_mod.main(argv)
            code = 0
        except SystemExit as e:
            code = e.code
    return code, buf.getvalue()


def test_cli_dry_run_changes_nothing(monkeypatch, tmp_path):
    week = tmp_path / "week.json"
    week.write_text(json.dumps(WEEK))
    fake = FakeApi()
    monkeypatch.setattr(api, "_request", fake)
    monkeypatch.setattr(cli_mod, "_token", lambda args: "tok")
    state = tmp_path / "state.json"
    code, out = _run(["personal-time", "sync", "--from", str(week),
                      "--state", str(state)])
    assert code == 0
    assert "create 3" in out and "skipped 1" in out
    assert fake.ops() == []
    assert not state.exists()


def test_cli_apply_without_token_stops_with_login_hint(monkeypatch, tmp_path):
    week = tmp_path / "week.json"
    week.write_text(json.dumps(WEEK))
    monkeypatch.setattr(cli_mod, "_token", lambda args: None)
    code, out = _run(["personal-time", "sync", "--from", str(week),
                      "--state", str(tmp_path / "s.json"), "--apply"])
    assert code == 1
    assert "python3 -m reinvent26 login" in out


def test_cli_apply_twice_is_idempotent(monkeypatch, tmp_path):
    week = tmp_path / "week.json"
    week.write_text(json.dumps(WEEK))
    fake = FakeApi()
    monkeypatch.setattr(api, "_request", fake)
    monkeypatch.setattr(cli_mod, "_token", lambda args: "tok")
    argv = ["personal-time", "sync", "--from", str(week),
            "--state", str(tmp_path / "s.json"), "--apply"]
    code, out = _run(argv)
    assert code == 0 and "appear exactly once" in out
    code, out = _run(argv)
    assert code == 0 and "unchanged 3" in out
    assert fake.ops().count("POST") == 3
    assert len(fake.live) == 3
