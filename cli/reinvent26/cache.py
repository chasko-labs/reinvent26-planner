"""Local catalog cache plus rust pre-filter pipe.

Stdlib only. Cached catalogs live under `.cache/<eventId>/sessions.json`
relative to the current working directory (gitignored; never commit them).
The rust helper (`rust/catalog-filter`) is an optional pre-filter: when its
binary is present, `--cached` shortlists pipe cached json through it before
python ranking. When the binary is absent, python filters directly.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys

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


def curated_dir() -> str:
    """Return the absolute path to data/reinvent2026 under repo root."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(repo_root, "data", "reinvent2026")


def load_curated_sessions(paths: list | None = None) -> list:
    """Load curated sessions from json files.

    If paths given, load each json file; else glob curated_dir()/*.json
    sorted by name. Each file must be a json array; skip (warn to stderr)
    non-array or unreadable files. Merge into one list, dedup by sessionId
    with later files winning. Rows without sessionId are kept as-is.
    Returns [] when curated_dir() is absent.
    """
    if paths is None:
        cdir = curated_dir()
        if not os.path.isdir(cdir):
            return []
        paths = sorted(glob.glob(os.path.join(cdir, "*.json")))

    merged: list = []
    seen_session_ids: dict = {}

    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as e:
            print(f"warning: skipping unreadable file {path}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, list):
            print(f"warning: skipping non-array file {path}", file=sys.stderr)
            continue
        for row in data:
            if not isinstance(row, dict):
                merged.append(row)
                continue
            sid = row.get("sessionId")
            if sid is None:
                merged.append(row)
            elif sid in seen_session_ids:
                idx = seen_session_ids[sid]
                merged[idx] = row
            else:
                seen_session_ids[sid] = len(merged)
                merged.append(row)

    return merged


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
