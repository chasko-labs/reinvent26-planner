import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import seeds  # noqa: E402


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def test_derive_counts_unigrams_skips_code_and_stopwords(tmp_path):
    blog = tmp_path / "blog"
    blog.mkdir()
    _write(blog / "a.md",
           "# bedrock agents\n\nbedrock agents ship. the and for.\n\n```\nbedrock_secret = 1\n```\n")
    _write(blog / "b.md", "agents everywhere, bedrock again\n")
    out = seeds.derive_seeds(str(tmp_path), top=5)
    assert out[0] == "agents"
    assert out[1] == "bedrock"
    assert "the" not in out and "bedrock_secret" not in out


def test_derive_is_deterministic(tmp_path):
    (tmp_path / "blog").mkdir()
    _write(tmp_path / "blog" / "a.md", "lambda serverless lambda containers\n")
    first = seeds.derive_seeds(str(tmp_path))
    assert seeds.derive_seeds(str(tmp_path)) == first


def test_save_load_roundtrip(tmp_path):
    path = str(tmp_path / "seeds.json")
    seeds.save_seeds(["agents", "bedrock"], path)
    assert seeds.load_seeds(path) == ["agents", "bedrock"]


def test_load_missing_or_bad_returns_empty(tmp_path):
    assert seeds.load_seeds(str(tmp_path / "nope.json")) == []
    bad = tmp_path / "bad.json"
    _write(bad, "{not json")
    assert seeds.load_seeds(str(bad)) == []
    wrong = tmp_path / "wrong.json"
    _write(wrong, json.dumps({"topics": "agents"}))
    assert seeds.load_seeds(str(wrong)) == []


def test_explicit_topics_override_seeds(tmp_path, monkeypatch):
    from reinvent26 import cli as cli_mod
    seed_file = tmp_path / "seeds.json"
    _write(seed_file, json.dumps({"topics": ["quantum"]}))
    monkeypatch.setattr(seeds, "seed_path", lambda: str(seed_file))
    ns = cli_mod.build_parser().parse_args(
        ["shortlist", "evt", "--topics", "agents,bedrock"])
    assert cli_mod._resolve_topics(ns) == ["agents", "bedrock"]
    ns = cli_mod.build_parser().parse_args(["shortlist", "evt"])
    assert cli_mod._resolve_topics(ns) == ["quantum"]
