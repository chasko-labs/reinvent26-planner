import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import api  # noqa: E402
from reinvent26 import cli as cli_mod  # noqa: E402


def _raise_404(*a, **k):
    raise api.EventsError(404, "not found")


def _raise_500(*a, **k):
    raise api.EventsError(500, "boom")


def test_cancel_404_means_already_absent(monkeypatch):
    monkeypatch.setattr(api, "_request", _raise_404)
    assert api.cancel_reservation("evt", "tok", "s1") is False
    assert api.remove_favorite("evt", "tok", "s1") is False


def test_cancel_success_hits_delete_path(monkeypatch):
    seen = {}

    def fake(method, path, **kwargs):
        seen["method"] = method
        seen["path"] = path
        return {}

    monkeypatch.setattr(api, "_request", fake)
    assert api.cancel_reservation("evt", "tok", "s1") is True
    assert seen == {"method": "DELETE",
                    "path": "/v1/events/evt/reservations/s1"}


def test_remove_success_hits_delete_path(monkeypatch):
    seen = {}

    def fake(method, path, **kwargs):
        seen["method"] = method
        seen["path"] = path
        return {}

    monkeypatch.setattr(api, "_request", fake)
    assert api.remove_favorite("evt", "tok", "s1") is True
    assert seen == {"method": "DELETE",
                    "path": "/v1/events/evt/favorites/s1"}


def test_cancel_other_errors_raise(monkeypatch):
    monkeypatch.setattr(api, "_request", _raise_500)
    with pytest.raises(api.EventsError):
        api.cancel_reservation("evt", "tok", "s1")


def _run_cmd(monkeypatch, cmd, fn_results, schedule_items):
    calls = {"n": 0}

    def fake_fn(event_id, token, session_id):
        result = fn_results[min(calls["n"], len(fn_results) - 1)]
        calls["n"] += 1
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(api, "cancel_reservation", fake_fn)
    monkeypatch.setattr(api, "remove_favorite", fake_fn)
    monkeypatch.setattr(api, "get_schedule",
                        lambda *a, **k: {"items": schedule_items})
    monkeypatch.setattr(cli_mod, "_catalog_for_confirm", lambda *a: [])
    args = cli_mod.build_parser().parse_args(cmd)
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        args.fn(args)  # must not raise: exit 0 path
    return buf.getvalue()


def test_remove_twice_second_reports_already_complete(monkeypatch):
    out1 = _run_cmd(monkeypatch,
                    ["remove-favorite", "evt", "s1"], [True], [])
    out2 = _run_cmd(monkeypatch,
                    ["remove-favorite", "evt", "s1"], [False], [])
    assert "removed; confirm" in out1
    assert "already absent: complete" in out2


def test_unknown_outcome_reconciles_absent_as_complete(monkeypatch):
    out = _run_cmd(monkeypatch,
                   ["cancel-reservation", "evt", "s1"],
                   [api.EventsError(500, "boom")], [])
    assert "treated as complete" in out


def test_unknown_outcome_reraises_when_still_present(monkeypatch):
    monkeypatch.setattr(api, "cancel_reservation", _raise_500)
    monkeypatch.setattr(api, "get_schedule",
                        lambda *a, **k: {"items": [{"sessionId": "s1"}]})
    monkeypatch.setattr(cli_mod, "_catalog_for_confirm", lambda *a: [])
    args = cli_mod.build_parser().parse_args(
        ["cancel-reservation", "evt", "s1"])
    with pytest.raises(api.EventsError):
        args.fn(args)
