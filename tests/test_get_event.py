"""get_event envelope handling (network stubbed)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import api  # noqa: E402


def test_get_event_unwraps_envelope_variants(monkeypatch):
    seen = {}

    def fake(method, path, token=None, params=None):
        seen["path"] = path
        return {"event": {"eventId": "reinvent2026", "eventName": "re:Invent", "timeZone": "America/Los_Angeles"}}

    monkeypatch.setattr(api, "_request", fake)
    got = api.get_event("reinvent2026")
    assert seen["path"] == "/v1/events/reinvent2026"
    assert got["eventName"] == "re:Invent"
    assert got["timeZone"] == "America/Los_Angeles"


def test_get_event_passes_through_bare_event(monkeypatch):
    monkeypatch.setattr(api, "_request",
                        lambda *a, **k: {"eventId": "x", "name": "X"})
    assert api.get_event("x")["name"] == "X"


def test_get_event_empty_envelope_gives_empty_dict(monkeypatch):
    monkeypatch.setattr(api, "_request", lambda *a, **k: {"items": []})
    assert api.get_event("x") == {"items": []}
