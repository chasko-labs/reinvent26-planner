import json
import os
import sys
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import cache, launches  # noqa: E402
from reinvent26.export_week import build_week  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "whats-new.xml")

CATALOG = [
    {"abbreviation": "STG301", "title": "Deep dive on Amazon S3 Tables", "abstract": ""},
    {"abbreviation": "CMP201", "title": "Serverless", "abstract": "Using AWS Lambda at scale"},
    {"abbreviation": "AIM999", "title": "Agents", "services": ["Bedrock AgentCore"]},
    {"abbreviation": "NET100", "title": "Networking basics", "abstract": "vpc"},
]


def _raw():
    with open(FIXTURE, "rb") as fh:
        return fh.read()


def _isolate(monkeypatch, tmp_path, catalog=None):
    path = tmp_path / "launches.json"
    monkeypatch.setattr(launches, "cache_path", lambda event_id: str(path))
    monkeypatch.setattr(cache, "load_cached_sessions", lambda event_id: catalog)
    return path


def test_parse_and_window():
    items = launches.parse_feed(_raw())
    assert len(items) == 5
    lo, hi = launches.window()
    assert lo.isoformat() == "2026-11-16"
    kept = {i["guid"] for i in launches.in_window(items, lo, hi)}
    assert kept == {"guid-s3tables", "guid-lambda"}


def test_keywords_and_matching():
    item = {"title": "Amazon S3 Tables now supports compaction"}
    assert "s3 tables" in launches.keywords(item["title"])
    assert launches.match_sessions(item, CATALOG) == ["STG301"]
    lam = {"title": "AWS Lambda adds new runtime"}
    assert launches.match_sessions(lam, CATALOG) == ["CMP201"]
    assert launches.match_sessions({"title": "no service here"}, CATALOG) == []


def test_run_writes_cache_and_dedupes(monkeypatch, tmp_path, capsys):
    path = _isolate(monkeypatch, tmp_path, CATALOG)
    assert launches.run("reinvent2026", "x", False, True, raw=_raw()) == 0
    rows = json.loads(capsys.readouterr().out)
    assert [r["title"] for r in rows][0].startswith("AWS Lambda")
    assert {c for r in rows for c in r["sessions"]} == {"STG301", "CMP201"}
    assert set(json.load(open(path))) == {"guid-s3tables", "guid-lambda"}
    assert launches.run("reinvent2026", "x", False, False, raw=_raw()) == 0
    assert "0 new" in capsys.readouterr().err
    assert len(json.load(open(path))) == 2


def test_dry_run_writes_nothing(monkeypatch, tmp_path):
    path = _isolate(monkeypatch, tmp_path, CATALOG)
    assert launches.run("reinvent2026", "x", True, False, raw=_raw()) == 0
    assert not path.exists()


def test_network_failure_exits_nonzero_writes_nothing(monkeypatch, tmp_path, capsys):
    path = _isolate(monkeypatch, tmp_path, CATALOG)

    def boom(*a, **k):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(launches.urllib.request, "urlopen", boom)
    assert launches.run("reinvent2026", "http://x", False, False) == 1
    captured = capsys.readouterr()
    assert "feed fetch failed" in captured.err
    assert captured.out == ""
    assert not path.exists()


def test_bad_xml_exits_nonzero(monkeypatch, tmp_path, capsys):
    path = _isolate(monkeypatch, tmp_path)
    assert launches.run("reinvent2026", "x", False, False, raw=b"<rss") == 1
    assert "parse failed" in capsys.readouterr().err
    assert not path.exists()


def test_export_week_emits_launches_and_signals():
    catalog = [{"sessionId": "a", "abbreviation": "NEW101",
                "title": "What's new in storage", "abstract": ""}]
    entries = [{"title": "T", "link": "L", "date": "2026-12-01", "sessions": ["NEW101"]}]
    week = build_week({"schedule": {}}, catalog, "/nonexistent", "2026-11-05", launches=entries)
    assert week["launches"] == entries
    assert week["launch_signals"][0]["code"] == "NEW101"
    assert week["launch_signals"][0]["signal"] == "title"
    json.dumps(week)
