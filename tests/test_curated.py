import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import cache  # noqa: E402


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def test_load_curated_sessions_merge_and_dedup_later_wins(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "reinvent2026"
    data_dir.mkdir(parents=True)
    a_file = data_dir / "a.json"
    b_file = data_dir / "b.json"
    _write_json(a_file, [
        {"sessionId": "s1", "title": "A1"},
        {"sessionId": "s2", "title": "A2"},
    ])
    _write_json(b_file, [
        {"sessionId": "s2", "title": "B2"},
        {"sessionId": "s3", "title": "B3"},
    ])
    monkeypatch.setattr(cache, "curated_dir", lambda: str(data_dir))
    sessions = cache.load_curated_sessions()
    assert len(sessions) == 3
    by_id = {s["sessionId"]: s for s in sessions}
    assert by_id["s1"]["title"] == "A1"
    assert by_id["s2"]["title"] == "B2"
    assert by_id["s3"]["title"] == "B3"


def test_load_curated_sessions_skip_non_array(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data" / "reinvent2026"
    data_dir.mkdir(parents=True)
    bad = data_dir / "bad.json"
    _write_json(bad, {"not": "array"})
    _write_json(data_dir / "good.json", [{"sessionId": "ok", "title": "ok"}])
    monkeypatch.setattr(cache, "curated_dir", lambda: str(data_dir))
    sessions = cache.load_curated_sessions()
    captured = capsys.readouterr()
    assert "warning" in captured.err
    assert "non-array" in captured.err
    assert len(sessions) == 1
    assert sessions[0]["sessionId"] == "ok"


def test_load_curated_sessions_skip_unreadable(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data" / "reinvent2026"
    data_dir.mkdir(parents=True)
    bad = data_dir / "bad.json"
    bad.write_text("{not json")
    _write_json(data_dir / "good.json", [{"sessionId": "ok", "title": "ok"}])
    monkeypatch.setattr(cache, "curated_dir", lambda: str(data_dir))
    sessions = cache.load_curated_sessions()
    captured = capsys.readouterr()
    assert "warning" in captured.err
    assert "unreadable" in captured.err
    assert len(sessions) == 1


def test_load_curated_sessions_absent_dir_returns_empty(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "reinvent2026"
    monkeypatch.setattr(cache, "curated_dir", lambda: str(data_dir))
    sessions = cache.load_curated_sessions()
    assert sessions == []


def test_load_curated_sessions_explicit_paths(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "reinvent2026"
    data_dir.mkdir(parents=True)
    _write_json(data_dir / "a.json", [{"sessionId": "a", "title": "A"}])
    _write_json(data_dir / "b.json", [{"sessionId": "b", "title": "B"}])
    monkeypatch.setattr(cache, "curated_dir", lambda: str(data_dir))
    sessions = cache.load_curated_sessions(paths=[str(data_dir / "a.json")])
    assert len(sessions) == 1
    assert sessions[0]["sessionId"] == "a"


def test_load_curated_sessions_no_session_id_kept_as_is(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "reinvent2026"
    data_dir.mkdir(parents=True)
    _write_json(data_dir / "a.json", [
        {"sessionId": "s1", "title": "S1"},
        {"title": "no-id"},
    ])
    monkeypatch.setattr(cache, "curated_dir", lambda: str(data_dir))
    sessions = cache.load_curated_sessions()
    assert len(sessions) == 2
    assert sessions[0]["sessionId"] == "s1"
    assert sessions[1].get("sessionId") is None
