"""Full-but-interesting ledger: topic sessions without an open seat, with presenters to follow.

Writes docs/full-but-interesting.md. Breakouts are flagged for the post-event YouTube upload;
re:Invent historically publishes breakout recordings, chalk talks and workshops are not recorded.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

from reinvent26 import mapper

OPEN = {"available", "limited", "veryLimited"}
RECORDED_TYPES = {"Breakout session", "Keynote", "Mainstage", "Lightning talk"}


def _root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_seats(root: str) -> dict:
    for name in ("seats-sweep.json", "seats-sweep-2026-10-29a.json", "seats.json"):
        try:
            with open(os.path.join(root, ".cache", "reinvent2026", name), encoding="utf-8") as fh:
                got = json.load(fh).get("seats", {})
                if len(got) > 1000:
                    return got
        except (OSError, ValueError):
            continue
    return {}


def build(catalog: list, config: dict, seats: dict, reserved: set) -> tuple:
    topics = config.get("topics", [])
    rows, speakers = [], defaultdict(set)
    for s in catalog:
        core, rel = mapper._tag(s, topics)
        if not (core or rel):
            continue
        if s.get("sessionId") in reserved:
            continue
        if mapper._is_bedrock_excluded(s, config) or mapper._is_frontier_excluded(s, config)[0]:
            continue
        seat = seats.get(s.get("abbreviation"))
        if s.get("isReservable") and seat in OPEN:
            continue  # bookable: the planner owns it
        status = "full" if s.get("isReservable") else "walk-up only"
        names = [sp.get("name") for sp in (s.get("speakers") or []) if sp.get("name")]
        for n in names:
            speakers[n].add(s.get("abbreviation"))
        rows.append({"s": s, "core": core, "rel": rel, "status": status, "names": names})
    return rows, speakers


def render(rows: list, speakers: dict, fetched: str) -> str:
    def when(s):
        st = s.get("sessionTime") or {}
        return (st.get("date") or "9999", st.get("time") or "")
    by_topic = defaultdict(list)
    for r in rows:
        by_topic[(r["core"] or r["rel"])[0]].append(r)
    out = ["# full but interesting", "",
           f"topic sessions we cannot hold a reserved seat in (seat data swept {fetched}). follow the presenters, and catch the breakouts on youtube after the event",
           "", "- full: reservable, no seat left. walk-up lines may still get in; not counted toward the reserved plan",
           "- walk-up only: never reservable",
           "- youtube: breakouts, lightning talks, and keynotes have historically been posted to the aws events channel after re:invent. chalk talks, workshops, and builders' sessions are not recorded (medium confidence, based on prior years)",
           "", f"sessions: {len(rows)}, presenters: {len(speakers)}", ""]
    for topic, grp in sorted(by_topic.items()):
        out += [f"## {topic}", "", "| code | day | time | venue | type | status | after the event | presenters | title |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in sorted(grp, key=lambda r: when(r["s"])):
            s = r["s"]
            d, t = when(s)
            after = "youtube" if s.get("type") in RECORDED_TYPES else "not recorded"
            out.append("| " + " | ".join([
                s.get("abbreviation", ""), d[5:] if d != "9999" else "tbd", t or "tbd", s.get("venue") or "tbd",
                s.get("type", ""), r["status"], after, ", ".join(r["names"]) or "tbd",
                (s.get("title") or "").replace("|", "/")]) + " |")
        out.append("")
    out += ["## presenters to follow", "", "names as listed in the catalog. sessions per presenter in the right column", "",
            "| presenter | sessions |", "| --- | --- |"]
    for name, codes in sorted(speakers.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        out.append(f"| {name} | {', '.join(sorted(codes))} |")
    return "\n".join(out) + "\n"


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="reinvent26 interest", description="write docs/full-but-interesting.md")
    p.add_argument("--out-dir", default=None)
    args = p.parse_args(argv)
    root = _root()
    catalog = json.load(open(os.path.join(root, ".cache", "reinvent2026", "catalog.json"), encoding="utf-8"))
    config = mapper._load_config()
    seats = _load_seats(root)
    try:
        sched = json.load(open(os.path.join(root, ".cache", "reinvent2026", "schedule.json"), encoding="utf-8"))
        reserved = set(sched["schedule"].get("reserved", []))
    except (OSError, ValueError, KeyError):
        reserved = set()
    rows, speakers = build(catalog, config, seats, reserved)
    out_dir = args.out_dir or os.path.join(root, "docs")
    path = os.path.join(out_dir, "full-but-interesting.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(rows, speakers, "2026-10-29"))
    print(f"{len(rows)} sessions, {len(speakers)} presenters -> {path}")
