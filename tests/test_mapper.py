"""Tests for the event map generator (mapper.py)."""
import json
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import mapper


def test_venue_gap_compatibility() -> None:
    """Test venue gap rules: same venue 0, cluster 30, mgm 60."""
    config = {
        "same_venue_gap": 0,
        "near_venue_gap": 30,
        "far_venue_gap": 60,
        "cluster_venues": ["Venetian", "Wynn/Encore", "Caesars Palace", "Caesars Forum"]
    }
    
    a = {"venue": "Venetian", "_end": datetime.fromisoformat("2026-12-01T10:00:00")}
    b = {"venue": "Venetian", "_start": datetime.fromisoformat("2026-12-01T10:00:00")}
    assert mapper._compatible(a, b, config)
    
    a = {"venue": "Venetian", "_end": datetime.fromisoformat("2026-12-01T10:00:00")}
    b = {"venue": "Wynn/Encore", "_start": datetime.fromisoformat("2026-12-01T10:25:00")}
    assert not mapper._compatible(a, b, config)
    
    a = {"venue": "Venetian", "_end": datetime.fromisoformat("2026-12-01T10:00:00")}
    b = {"venue": "Wynn/Encore", "_start": datetime.fromisoformat("2026-12-01T10:35:00")}
    assert mapper._compatible(a, b, config)
    
    a = {"venue": "Venetian", "_end": datetime.fromisoformat("2026-12-01T10:00:00")}
    b = {"venue": "MGM Grand", "_start": datetime.fromisoformat("2026-12-01T10:25:00")}
    assert not mapper._compatible(a, b, config)
    
    a = {"venue": "Venetian", "_end": datetime.fromisoformat("2026-12-01T10:00:00")}
    b = {"venue": "MGM Grand", "_start": datetime.fromisoformat("2026-12-01T11:05:00")}
    assert mapper._compatible(a, b, config)


def test_anchor_wins_over_heavier_non_anchor() -> None:
    """Test that anchors get priority boost."""
    config = {
        "topic_weight": {"amazon leo": 20},
        "anchors": ["amazon leo"],
        "pinned": [],
        "cluster_venues": ["Venetian"],
        "same_venue_gap": 0,
        "near_venue_gap": 30,
        "far_venue_gap": 60
    }
    
    s_anchor = {
        "_start": datetime.fromisoformat("2026-12-01T09:00:00"),
        "_end": datetime.fromisoformat("2026-12-01T10:00:00"),
        "_core": ["amazon leo"],
        "_fav": False,
        "isReservable": False,
        "level": "300",
        "abbreviation": "ANT001"
    }
    s_non_anchor = {
        "_start": datetime.fromisoformat("2026-12-01T11:00:00"),
        "_end": datetime.fromisoformat("2026-12-01T12:00:00"),
        "_core": ["netflix"],
        "_fav": True,
        "isReservable": True,
        "level": "400",
        "abbreviation": "NET001"
    }
    
    assert mapper._is_anchor(s_anchor, config)
    assert not mapper._is_anchor(s_non_anchor, config)
    w_anchor = mapper._weight(s_anchor, config)
    w_non_anchor = mapper._weight(s_non_anchor, config)
    assert w_anchor > w_non_anchor


def test_bedrock_exclusion_with_nova_exception() -> None:
    """Test bedrock exclusion with nova exception."""
    config = {
        "bedrock_excluded": True,
        "bedrock_keywords": ["bedrock", "agentcore"],
        "nova_exception": True
    }
    
    s_bedrock = {
        "title": "Building agents with Bedrock",
        "services": ["Amazon Bedrock"],
        "abstract": "This session covers Bedrock"
    }
    s_nova = {
        "title": "Amazon Nova models",
        "services": ["Amazon Nova"],
        "abstract": "Nova is great for AI"
    }
    s_bedrock_nova = {
        "title": "Nova Bedrock integration",
        "services": ["Amazon Bedrock", "Amazon Nova"],
        "abstract": "Nova and Bedrock together"
    }
    
    assert mapper._is_bedrock_excluded(s_bedrock, config)
    assert not mapper._is_bedrock_excluded(s_nova, config)
    assert not mapper._is_bedrock_excluded(s_bedrock_nova, config)


def test_repeat_dedupe() -> None:
    """Test that -R variants dedupe to base code."""
    assert mapper._base("ANT001") == "ANT001"
    assert mapper._base("ANT001-R") == "ANT001"
    assert mapper._base("ANT001-R1") == "ANT001"
    assert mapper._base("ANT001-R2") == "ANT001"


def test_missing_session_time_venue_skipped() -> None:
    """Test sessions without sessionTime or venue go to TBD."""
    config = {
        "topics": [],
        "cluster_venues": ["Venetian"],
        "same_venue_gap": 0,
        "near_venue_gap": 30,
        "far_venue_gap": 60
    }
    
    s_tbd = {
        "abbreviation": "ANT001",
        "title": "Session without time"
    }
    
    w = mapper._when(s_tbd)
    assert w is None
    assert not s_tbd.get("venue")


def test_tag_matches() -> None:
    """Test topic pattern matching."""
    config = {
        "topics": [
            {"name": "agents", "pattern": "agent|agents"},
            {"name": "storage", "pattern": "s3|storage"}
        ]
    }
    
    s = {
        "title": "Building agents with S3 storage",
        "abstract": "Agents and storage"
    }
    
    core, rel = mapper._tag(s, config["topics"])
    assert "agents" in core
    assert "storage" in core


def test_off_topic_session_excluded_from_all_buckets(tmp_path) -> None:
    """Off-topic sessions should not appear in pool, excluded, or tbd buckets."""
    config = {
        "topics": [
            {"name": "agents", "pattern": "agent|agents"},
            {"name": "open-weight models", "pattern": "llama|qwen", "abstract_pattern": "mistral|qwen"}
        ],
        "pinned": [],
        "bedrock_excluded": True,
        "bedrock_keywords": ["bedrock"],
        "nova_exception": True,
        "frontier_excluded": True,
        "frontier_title_patterns": ["frontier", "claude"],
        "frontier_abstract_keywords": ["claude"],
        "cluster_venues": ["Venetian"],
        "same_venue_gap": 0,
        "near_venue_gap": 30,
        "far_venue_gap": 60
    }
    
    # Off-topic session - no core, rel, fav, or pinned
    off_topic = {
        "abbreviation": "OFF001",
        "title": "Random session unrelated to any topic",
        "abstract": "This is just some random content",
        "sessionTime": {"date": "2026-12-01", "time": "10:00", "length": 60},
        "venue": "Venetian"
    }
    
    catalog = [off_topic]
    chosen, excluded, tbd, chosen_codes, reason_func, dayname = mapper._build_map(catalog, config, str(tmp_path))
    
    # Off-topic session should not appear in any output bucket
    assert off_topic not in chosen
    assert off_topic not in excluded
    assert off_topic not in tbd


def test_open_weight_abstract_pattern_produces_related_match(tmp_path) -> None:
    """Open-weight models topic should match abstract_pattern on abstract-only."""
    config = {
        "topics": [
            {"name": "open-weight models", "pattern": "llama|qwen", "abstract_pattern": "mistral|qwen"}
        ],
        "pinned": [],
        "bedrock_excluded": True,
        "bedrock_keywords": ["bedrock"],
        "nova_exception": True,
        "frontier_excluded": True,
        "frontier_title_patterns": ["frontier"],
        "frontier_abstract_keywords": ["claude"],
        "cluster_venues": ["Venetian"],
        "same_venue_gap": 0,
        "near_venue_gap": 30,
        "far_venue_gap": 60
    }
    
    # Session with no title match but abstract match for open-weight
    s = {
        "abbreviation": "OW001",
        "title": "Large language models comparison",
        "abstract": "We use mistral models for our inference pipeline",
        "sessionTime": {"date": "2026-12-01", "time": "10:00", "length": 60},
        "venue": "Venetian"
    }
    
    catalog = [s]
    chosen, excluded, tbd, chosen_codes, reason_func, dayname = mapper._build_map(catalog, config, str(tmp_path))
    
    # Should be in chosen with rel match
    assert s in chosen
    assert s.get("_rel") == ["open-weight models"]
    assert s.get("_core") == []


def test_frontier_title_excluded_dvt206_style(tmp_path) -> None:
    """Sessions with 'Frontier teams' in title should be excluded."""
    config = {
        "topics": [
            {"name": "agents", "pattern": "agent|agents"}
        ],
        "pinned": [],
        "bedrock_excluded": True,
        "bedrock_keywords": ["bedrock"],
        "nova_exception": True,
        "frontier_excluded": True,
        "frontier_title_patterns": ["frontier", "claude", "anthropic"],
        "frontier_abstract_keywords": ["claude"],
        "cluster_venues": ["Venetian"],
        "same_venue_gap": 0,
        "near_venue_gap": 30,
        "far_venue_gap": 60
    }
    
    # DVT206-style title with 'Frontier teams'; on-topic so it reaches the exclusion check
    s = {
        "abbreviation": "DVT206",
        "title": "Frontier teams building agents",
        "abstract": "This is about frontier technology",
        "sessionTime": {"date": "2026-12-01", "time": "10:00", "length": 60},
        "venue": "Venetian"
    }
    
    catalog = [s]
    chosen, excluded, tbd, chosen_codes, reason_func, dayname = mapper._build_map(catalog, config, str(tmp_path))
    
    # Should be excluded due to frontier title match
    assert s in excluded
    assert s.get("_exclude_reason") == "frontier"


def test_frontier_abstract_only_flagged_not_excluded(tmp_path) -> None:
    """Sessions with frontier keywords only in abstract should be flagged, not excluded."""
    config = {
        "topics": [
            {"name": "agents", "pattern": "agent|agents"}
        ],
        "pinned": [],
        "bedrock_excluded": True,
        "bedrock_keywords": ["bedrock"],
        "nova_exception": True,
        "frontier_excluded": True,
        "frontier_title_patterns": ["frontier", "claude"],
        "frontier_abstract_keywords": ["claude"],
        "cluster_venues": ["Venetian"],
        "same_venue_gap": 0,
        "near_venue_gap": 30,
        "far_venue_gap": 60
    }
    
    # Session with no title match but abstract match for frontier
    s = {
        "abbreviation": "AGT001",
        "title": "Building agents with agents framework",
        "abstract": "We use claude for reasoning tasks",
        "sessionTime": {"date": "2026-12-01", "time": "10:00", "length": 60},
        "venue": "Venetian"
    }
    
    catalog = [s]
    chosen, excluded, tbd, chosen_codes, reason_func, dayname = mapper._build_map(catalog, config, str(tmp_path))
    
    # Should be in chosen (not excluded) but flagged for abstract-only frontier mention
    assert s in chosen
    assert s.get("_exclude_reason") is None
    assert s.get("_frontier_abstract") is True


def test_main_requires_out_dir_under_pytest(tmp_path) -> None:
    """Test that main() raises error when --out-dir is missing under pytest."""
    # Create a minimal catalog file
    catalog_path = tmp_path / "test_catalog.json"
    catalog_data = [
        {
            "abbreviation": "TST001",
            "title": "Test Session",
            "sessionTime": {"date": "2026-12-01", "time": "10:00", "length": 60},
            "venue": "Venetian"
        }
    ]
    catalog_path.write_text(json.dumps(catalog_data))
    
    # Simulate pytest environment
    old_environ = os.environ.get("PYTEST_CURRENT_TEST")
    try:
        os.environ["PYTEST_CURRENT_TEST"] = "tests/test_mapper.py::test_main_requires_out_dir_under_pytest"
        
        # Should raise SystemExit when --out-dir is missing
        with pytest.raises(SystemExit) as exc_info:
            mapper.main(["--catalog", str(catalog_path)])
        
        # Exit code should be 2 for missing out-dir
        assert exc_info.value.code == 2
    finally:
        if old_environ is None:
            os.environ.pop("PYTEST_CURRENT_TEST", None)
        else:
            os.environ["PYTEST_CURRENT_TEST"] = old_environ


def test_main_works_with_explicit_out_dir(tmp_path) -> None:
    """Test that main() works with explicit --out-dir."""
    # Create a minimal catalog file
    catalog_path = tmp_path / "test_catalog.json"
    catalog_data = [
        {
            "abbreviation": "TST001",
            "title": "Test Session",
            "sessionTime": {"date": "2026-12-01", "time": "10:00", "length": 60},
            "venue": "Venetian"
        }
    ]
    catalog_path.write_text(json.dumps(catalog_data))
    
    out_dir = tmp_path / "output"
    
    # Should not raise
    mapper.main(["--catalog", str(catalog_path), "--out-dir", str(out_dir)])
    
    # Output files should exist
    assert (out_dir / "event-map.md").exists()
    assert (out_dir / "launch-ledger.md").exists()
