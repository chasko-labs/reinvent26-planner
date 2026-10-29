"""Tests for the event map generator (mapper.py)."""
import json
import os
import sys
from datetime import datetime, timedelta

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
