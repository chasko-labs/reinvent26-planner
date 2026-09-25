"""Read-only live-stack inventory for the stack-aware picker (issue #7).

All reads are read-only. Live reads shell out to the ``aws`` CLI
(resourcegroupstaggingapi get-resources, describe calls only) with an
explicit ``--profile``; this module never issues a write call and never
accepts or forwards access tokens.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter


def load_resources_file(path: str) -> list:
    """Load resources from a cached AWS CLI JSON file.

    Accepts a bare JSON array, or a dict wrapping one under a known key
    (ResourceTagMappingList, ResourceDescriptions, Stacks, Reservations).
    Returns the resource list (possibly empty).
    """
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in (
            "ResourceTagMappingList",
            "ResourceDescriptions",
            "Stacks",
            "Reservations",
            "resources",
            "items",
        ):
            val = raw.get(key)
            if isinstance(val, list):
                return val
        return [raw]
    return []


def fetch_via_aws_cli(profile: str, region: str | None = None) -> list:
    """Read-only resource inventory via the AWS CLI.

    Requires an explicit profile so the agent stays on a named read-only
    role even when the default chain could write. Raises ValueError when
    no profile is given, FileNotFoundError when the ``aws`` CLI is missing.
    """
    if not (profile or "").strip():
        raise ValueError("explicit --profile is required for live stack reads")
    cmd = [
        "aws",
        "resourcegroupstaggingapi",
        "get-resources",
        "--profile",
        profile.strip(),
        "--output",
        "json",
    ]
    if region:
        cmd += ["--region", region]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"aws cli failed: {proc.stderr.strip()[:300]}")
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"aws cli returned non-json output: {e}") from e
    items = payload.get("ResourceTagMappingList")
    return items if isinstance(items, list) else []


def summarize_inventory(resources: list) -> list:
    """Count resources by type ARN/name for the picker report."""
    counts: Counter = Counter()
    for r in resources:
        if not isinstance(r, dict):
            continue
        rtype = (
            r.get("ResourceType")
            or r.get("ResourceARN")
            or r.get("service")
            or r.get("type")
            or "unknown"
        )
        counts[str(rtype)] += 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
