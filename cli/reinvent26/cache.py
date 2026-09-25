"""Local catalog cache plus rust pre-filter pipe.

Stdlib only. Cached catalogs live under `.cache/<eventId>/sessions.json`
relative to the current working directory (gitignored; never commit them).
The rust helper (`rust/catalog-filter`) is an optional pre-filter: when its
binary is present, `--cached` shortlists pipe cached json through it before
python ranking. When the binary is absent, python filters directly.
"""

from __future__ import annotations

import json
import os
import subprocess

CACHE_DIR = ".cache"


def cache_file(event_id: str) -> str:
    return os.path.join(CACHE_DIR, event_id, "sessions.json")


def load_cached_sessions(event_id: str) -> list | None:
    """Return cached sessions, or None when no cache exists."""
    path = cache_file(event_id)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else None


def save_cached_sessions(event_id: str, sessions: list) -> str:
    """Write sessions to cache. Returns the cache path."""
    path = cache_file(event_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(sessions, fh)
    return path


def find_filter_binary() -> str | None:
    """Locate the catalog-filter binary, or None when not built."""
    candidates = []
    env = os.environ.get("CATALOG_FILTER_BIN")
    if env:
        candidates.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    candidates.append(
        os.path.join(repo_root, "rust", "catalog-filter", "target", "release", "catalog-filter")
    )
    for rel in (
        os.path.join("rust", "catalog-filter", "target", "release", "catalog-filter"),
        os.path.join("..", "rust", "catalog-filter", "target", "release", "catalog-filter"),
        os.path.join("target", "release", "catalog-filter"),
    ):
        candidates.append(os.path.abspath(rel))
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def rust_prefilter(
    raw: bytes,
    topics: list | None = None,
    levels: list | None = None,
    day: str | None = None,
) -> list | None:
    """Pipe cached catalog json through the rust helper.

    Returns the matching session list, or None when the binary is absent
    or fails (caller falls back to python filtering).
    """
    binary = find_filter_binary()
    if binary is None:
        return None
    cmd = [binary]
    if topics:
        cmd += ["--topics", ",".join(topics)]
    if levels:
        cmd += ["--levels", ",".join(levels)]
    if day:
        cmd += ["--day", day]
    try:
        proc = subprocess.run(
            cmd, input=raw, capture_output=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout.decode())
    except ValueError:
        return None
    return data if isinstance(data, list) else None
