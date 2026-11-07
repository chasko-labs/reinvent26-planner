"""AWS What's New launch feed, cross-referenced to catalog sessions.

`python3 -m reinvent26 launches [event_id] [--dry-run] [--json]`

Reads the public What's New RSS feed (no auth), keeps items dated inside
the event window plus 14 days before, merges them into a cache file, and
matches each item to catalog sessions by service keyword.

Inputs
  feed url (default FEED_URL), cached catalog (`sessions` or `ingest` first;
  an absent catalog just yields no matches)

Side effects (unless --dry-run)
  writes <repo>/.cache/<event>/launches.json: guid -> item record. The cache
  keeps items after they roll off the feed and marks which are new this run.

Fails fast
  exit 1: feed unreachable or unparseable; message on stderr, nothing written
"""

from __future__ import annotations

import argparse
import datetime as _dt
import email.utils
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from reinvent26 import cache

EVENT_ID = "reinvent2026"
FEED_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
EVENT_START = _dt.date(2026, 11, 30)
EVENT_END = _dt.date(2026, 12, 4)
LEAD_DAYS = 14
TIMEOUT = 20

SERVICE_RE = re.compile(
    r"\b(?:Amazon|AWS)\s+((?:[A-Z0-9][\w.-]*)(?:\s+[A-Z0-9][\w.-]*){0,3})")
GENERIC = {"elastic", "simple", "managed", "web", "new", "amazon", "aws",
           "the", "for", "now", "service", "services"}


class FeedError(RuntimeError):
    """Feed fetch or parse failure."""


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def cache_path(event_id: str) -> str:
    return os.path.join(repo_root(), ".cache", event_id, "launches.json")


def fetch_feed(url: str = FEED_URL, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "reinvent26-planner"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise FeedError(f"feed fetch failed: {exc}") from exc


def parse_feed(raw: bytes) -> list:
    """RSS bytes to [{guid, title, link, date}]; items without a date are dropped."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise FeedError(f"feed parse failed: {exc}") from exc
    items = []
    for node in root.iter("item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        guid = (node.findtext("guid") or link or title).strip()
        stamp = (node.findtext("pubDate") or "").strip()
        try:
            date = email.utils.parsedate_to_datetime(stamp).date().isoformat()
        except (TypeError, ValueError):
            continue
        if title and guid:
            items.append({"guid": guid, "title": title, "link": link, "date": date})
    return items


def window(start: _dt.date = EVENT_START, end: _dt.date = EVENT_END,
           lead_days: int = LEAD_DAYS) -> tuple:
    return start - _dt.timedelta(days=lead_days), end


def in_window(items: list, lo: _dt.date, hi: _dt.date) -> list:
    return [i for i in items if lo.isoformat() <= i["date"] <= hi.isoformat()]


def keywords(title: str) -> list:
    """Service-name keyword candidates from a launch title, longest first."""
    found = set()
    for m in SERVICE_RE.finditer(title):
        tokens = m.group(1).split()
        for n in range(1, len(tokens) + 1):
            phrase = " ".join(tokens[:n]).lower()
            if n == 1 and phrase in GENERIC:
                continue
            if len(phrase) >= 4 or any(c.isdigit() for c in phrase):
                found.add(phrase)
    return sorted(found, key=lambda k: (-len(k), k))


def match_sessions(item: dict, catalog: list) -> list:
    """Session codes whose title, abstract, or services mention an item keyword."""
    kws = keywords(item.get("title", ""))
    if not kws:
        return []
    patterns = [re.compile(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])") for k in kws]
    codes = []
    for s in catalog:
        if not isinstance(s, dict):
            continue
        hay = " ".join([s.get("title") or "", s.get("abstract") or "",
                        " ".join(s.get("services") or [])]).lower()
        if any(p.search(hay) for p in patterns):
            code = s.get("abbreviation") or s.get("code") or s.get("sessionId")
            if code and code not in codes:
                codes.append(code)
    return sorted(codes)


def load_cache(event_id: str) -> dict:
    try:
        with open(cache_path(event_id), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def merge(cached: dict, fresh: list) -> tuple:
    """Dedupe by guid. Returns (merged dict, set of new guids)."""
    merged = dict(cached)
    new = set()
    for item in fresh:
        if item["guid"] not in merged:
            new.add(item["guid"])
        merged[item["guid"]] = {k: item[k] for k in ("guid", "title", "link", "date")}
    return merged, new


def launch_list(records, catalog: list, lo: _dt.date, hi: _dt.date) -> list:
    """Windowed launches with matched session codes, newest first."""
    rows = in_window(list(records), lo, hi)
    out = [{"title": r["title"], "link": r["link"], "date": r["date"],
            "sessions": match_sessions(r, catalog)} for r in rows]
    out.sort(key=lambda r: (r["date"], r["title"]), reverse=True)
    return out


def cached_launches(event_id: str, catalog: list) -> list:
    """Offline view for export_week: cached launches matched to the catalog."""
    lo, hi = window()
    return launch_list(load_cache(event_id).values(), catalog, lo, hi)


def run(event_id: str, url: str, dry_run: bool, as_json: bool,
        raw: bytes | None = None) -> int:
    try:
        raw = raw if raw is not None else fetch_feed(url)
        fresh = parse_feed(raw)
    except FeedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    lo, hi = window()
    fresh = in_window(fresh, lo, hi)
    merged, new = merge(load_cache(event_id), fresh)
    catalog = cache.load_cached_sessions(event_id) or []
    rows = launch_list(merged.values(), catalog, lo, hi)
    new_links = {merged[g]["link"] for g in new}
    if as_json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            flag = "new " if r["link"] in new_links else "    "
            print(f"{flag}{r['date']} {r['title']} [{', '.join(r['sessions'])}]")
    matched = sum(1 for r in rows if r["sessions"])
    print(f"# launches: {len(rows)} in window {lo}..{hi}, {len(new)} new, "
          f"{matched} matched to sessions", file=sys.stderr)
    if not dry_run:
        path = cache_path(event_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(merged, fh)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="reinvent26 launches",
                                     description="AWS What's New launches in the event window, matched to sessions")
    parser.add_argument("event_id", nargs="?", default=EVENT_ID)
    parser.add_argument("--feed-url", default=FEED_URL)
    parser.add_argument("--dry-run", action="store_true", help="print, write no cache")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    return run(args.event_id, args.feed_url, args.dry_run, args.as_json)


if __name__ == "__main__":
    raise SystemExit(main())
