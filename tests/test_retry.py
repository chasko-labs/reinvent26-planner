import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

import pytest  # noqa: E402

from reinvent26 import api  # noqa: E402


def _scripted(monkeypatch, outcomes):
    """outcomes: list of values to return or Exceptions to raise."""
    calls = {"n": 0, "sleeps": []}
    monkeypatch.setattr(api, "_sleep", lambda s: calls["sleeps"].append(s))

    def fake(*a, **k):
        outcome = outcomes[min(calls["n"], len(outcomes) - 1)]
        calls["n"] += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(api, "_request", fake)
    return calls


def test_forced_429_read_sleeps_retry_after_then_succeeds(monkeypatch):
    calls = _scripted(monkeypatch, [api.EventsError(429, "slow", 7.0),
                                    {"ok": True}])
    assert api.read_with_retry(api._request) == {"ok": True}
    assert calls["sleeps"] == [7.0]
    assert calls["n"] == 2


def test_read_backs_off_1s_2s_on_500_then_succeeds(monkeypatch):
    calls = _scripted(monkeypatch, [api.EventsError(500, "x"),
                                    api.EventsError(503, "y"),
                                    {"ok": True}])
    assert api.read_with_retry(api._request) == {"ok": True}
    assert calls["sleeps"] == [1.0, 2.0]


def test_read_never_retries_403(monkeypatch):
    calls = _scripted(monkeypatch, [api.EventsError(403, "not registered")])
    with pytest.raises(api.EventsError):
        api.read_with_retry(api._request)
    assert calls["n"] == 1 and calls["sleeps"] == []


def test_write_429_retries_once_but_500_never_retries(monkeypatch):
    calls = _scripted(monkeypatch, [api.EventsError(429, "slow", 3.0),
                                    {"batch": "ok"}])
    assert api.write_with_retry_429(api._request) == {"batch": "ok"}
    assert calls["sleeps"] == [3.0]

    calls = _scripted(monkeypatch, [api.EventsError(500, "boom")])
    with pytest.raises(api.EventsError):
        api.write_with_retry_429(api._request)
    assert calls["n"] == 1 and calls["sleeps"] == []


def test_delete_retries_once_on_500_then_404_is_complete(monkeypatch):
    calls = _scripted(monkeypatch, [api.EventsError(500, "boom"),
                                    api.EventsError(404, "gone")])
    assert api.remove_favorite("evt", "tok", "s1") is False
    assert calls["n"] == 2


def test_delete_reraises_after_second_500(monkeypatch):
    calls = _scripted(monkeypatch, [api.EventsError(500, "a"),
                                    api.EventsError(500, "b")])
    with pytest.raises(api.EventsError):
        api.cancel_reservation("evt", "tok", "s1")
    assert calls["n"] == 2


def test_favorite_batch_honors_retry_after(monkeypatch):
    calls = _scripted(monkeypatch, [api.EventsError(429, "slow", 2.0),
                                    {"favorited": ["s1"]}])
    out = api.favorite_sessions("evt", "tok", ["s1"])
    assert out == [{"favorited": ["s1"]}]
    assert calls["sleeps"] == [2.0]
