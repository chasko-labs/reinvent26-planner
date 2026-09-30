import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import cache  # noqa: E402

SAMPLE = [
    {"sessionId": "a", "title": "agents with bedrock",
     "startTime": "2026-12-01T09:00:00", "endTime": "2026-12-01T10:00:00"},
    {"sessionId": "b", "title": "s3 deep dive",
     "startTime": "2026-12-02T09:00:00", "endTime": "2026-12-02T10:00:00"},
]


def test_cache_roundtrip_in_tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cache.load_cached_sessions("evt") is None
    path = cache.save_cached_sessions("evt", SAMPLE)
    assert path == os.path.join(".cache", "evt", "sessions.json")
    assert cache.load_cached_sessions("evt") == SAMPLE


def test_rust_prefilter_falls_back_without_binary(monkeypatch):
    monkeypatch.setattr(cache, "find_filter_binary", lambda: None)
    assert cache.rust_prefilter(b"[]", topics=["agents"]) is None


def test_rust_prefilter_uses_real_binary_when_built(monkeypatch):
    binary = cache.find_filter_binary()
    if binary is None:
        monkeypatch.setattr(
            cache, "find_filter_binary", lambda: None,
        )
        assert cache.rust_prefilter(b"[]") is None
        return
    raw = json.dumps(SAMPLE).encode()
    out = cache.rust_prefilter(raw, topics=["agents"])
    assert [s["sessionId"] for s in out] == ["a"]
    out = cache.rust_prefilter(raw, topics=["agents"], day="2026-12-02")
    assert out == []
