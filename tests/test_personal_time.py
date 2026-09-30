import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import api  # noqa: E402
from reinvent26 import cli as cli_mod  # noqa: E402
from reinvent26.schedule import validate_personal_time  # noqa: E402

OK = ("Lunch", "2026-12-01T12:00:00", "2026-12-01T13:00:00")


def test_validate_ok():
    validate_personal_time(*OK)


def test_validate_rejects_each_rule():
    with pytest.raises(ValueError):
        validate_personal_time("", *OK[1:])
    with pytest.raises(ValueError):
        validate_personal_time("x" * 129, *OK[1:])
    with pytest.raises(ValueError):
        validate_personal_time("Lunch", "2026-12-01T12:00:00Z", OK[2])
    with pytest.raises(ValueError):
        validate_personal_time("Lunch", "2026-12-01 12:00:00", OK[2])
    with pytest.raises(ValueError):
        validate_personal_time("Lunch", "2026-12-01T12:00:30", OK[2])
    with pytest.raises(ValueError):
        validate_personal_time("Lunch", OK[2], OK[1])
    with pytest.raises(ValueError):
        validate_personal_time("Lunch", "2026-12-01T12:00:00",
                               "2026-12-01T12:07:00")
    with pytest.raises(ValueError):
        validate_personal_time("Lunch", "2026-13-01T12:00:00", OK[2])


def test_reblock_sends_every_field_location_clears(monkeypatch):
    seen = {}

    def fake(method, path, token=None, params=None, body=None):
        seen["method"] = method
        seen["path"] = path
        seen["body"] = body
        return {}

    monkeypatch.setattr(api, "_request", fake)
    api.replace_personal_time("evt", "tok", "b1", *OK)
    assert seen["method"] == "PUT"
    assert seen["path"] == "/v1/events/evt/personal-time/b1"
    assert seen["body"] == {"title": "Lunch", "startDateTime": OK[1],
                            "endDateTime": OK[2], "description": "",
                            "location": None}


def test_block_cli_reads_new_id_from_schedule(monkeypatch):
    monkeypatch.setattr(api, "_request", lambda *a, **k: {})
    states = iter([{"items": []},
                   {"items": [{"sessionId": "pt-9", "title": "Lunch",
                               "start": OK[1]}]}])
    monkeypatch.setattr(api, "get_schedule", lambda *a, **k: next(states))
    monkeypatch.setattr(cli_mod, "_catalog_for_confirm", lambda *a: [])
    args = cli_mod.build_parser().parse_args(
        ["block", "evt", "--title", "Lunch", "--start", OK[1], "--end", OK[2]])
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        args.fn(args)
    assert "pt-9" in buf.getvalue()


def test_block_cli_rejects_bad_input():
    args = cli_mod.build_parser().parse_args(
        ["block", "evt", "--title", "Lunch", "--start", OK[1],
         "--end", "2026-12-01T12:07:00"])
    with pytest.raises(SystemExit):
        args.fn(args)


def test_unblock_404_is_complete(monkeypatch):
    def fake(method, path, **kwargs):
        raise api.EventsError(404, "gone")

    monkeypatch.setattr(api, "_request", fake)
    args = cli_mod.build_parser().parse_args(["unblock", "evt", "b1"])
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        args.fn(args)  # exit 0 path
    assert "already absent: complete" in buf.getvalue()
