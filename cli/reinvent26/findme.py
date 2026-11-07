"""Shareable find-me page: held seats, open windows, and visitor prompts.

`python3 -m reinvent26 find-me reinvent2026` prints markdown you can
paste anywhere: when bryan is free, what he wants to talk about, and
what to ask him. `--day 1` asks what visitors are most excited to see;
`--day 3` and up asks for the best thing seen so far.

Reads the live schedule and the cached catalog (run `sessions` first).
Read-only: never reserves, favorites, or writes personal time.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys

from reinvent26 import api, auth, cache, cli, mapper, schedule

EVENT_ID = "reinvent2026"
MIN_GAP_MINUTES = 60  # windows shorter than this are travel, not meetups


def talk_topics(items: list, config: dict) -> list:
    """Topic names present in the week, most-held first."""
    counts: dict = {}
    for s in items:
        core, _ = mapper._tag(s, config.get("topics", []))
        for t in core:
            counts[t] = counts.get(t, 0) + 1
    names = [t.get("name", "") for t in config.get("topics", []) if t.get("name")]
    return sorted(counts, key=lambda t: (-counts[t], names.index(t) if t in names else 99))


def day_gaps(held: list) -> list:
    """Open windows between same-day held seats, longest first.

    Each row: (date, start, end, minutes, part-of-day). Part of day
    follows the window start: morning before 12, midday before 17,
    evening after.
    """
    by_day: dict = {}
    for s in held:
        try:
            start = schedule._parse(s["startTime"])
            end = schedule._parse(s["endTime"])
        except (ValueError, KeyError):
            continue
        by_day.setdefault(start.date(), []).append((start, end))
    gaps = []
    for day, spans in by_day.items():
        spans.sort()
        for (_, prev_end), (next_start, _) in zip(spans, spans[1:]):
            minutes = int((next_start - prev_end).total_seconds() // 60)
            if minutes >= MIN_GAP_MINUTES:
                hour = prev_end.hour
                part = "morning" if hour < 12 else "midday" if hour < 17 else "evening"
                gaps.append((day, prev_end, next_start, minutes, part))
    gaps.sort(key=lambda g: (g[0], g[1]))
    return gaps


def visitor_prompt(day: int | None) -> str:
    """What to ask bryan, picked by event day."""
    base = ("tell him one architecture or topic you want to chat about — "
            "he keeps a list and will find you if a session fits it.")
    if day is not None and day >= 3:
        return base + " then tell him the best thing you have seen so far."
    if day == 2:
        return base + " then tell him the best thing you have seen so far, or what you are excited for next."
    return base + " if it is day 1, tell him what you are most excited to see."


def render_findme(date: str, held: list, gaps: list, topics: list, day: int | None) -> str:
    """Shareable markdown: week, windows, topics, visitor prompt."""
    lines = [f"# find bryan at re:invent ({date})", "",
             "chat with him about: " + (", ".join(topics) if topics else "anything on his schedule below."),
             ""]
    lines += ["## held seats", ""]
    for s in sorted(held, key=lambda x: x.get("startTime", "")):
        lines.append(f"- {(s.get('startTime') or '')[:16]} {(s.get('abbreviation') or s.get('code') or '?')} "
                     f"({s.get('venue', '?')}) — {s.get('title', '')}")
    lines += ["", "## open windows (morning, midday, evening)", ""]
    if gaps:
        for d, start, end, minutes, part in gaps:
            lines.append(f"- {d} {part}: {start:%H:%M}-{end:%H:%M} ({minutes} min)")
    else:
        lines.append("none over an hour. catch him between sessions.")
    lines += ["", "## if you find him", "", visitor_prompt(day)]
    return "\n".join(lines) + "\n"


def run(event_id: str, day: int | None, out: str | None) -> int:
    """Fetch the schedule, render the page, print or write it."""
    token = auth.stored_access_token()
    if not token:
        print("error: no valid token; run `python3 -m reinvent26 login` first", file=sys.stderr)
        return 2
    catalog = cache.load_cached_sessions(event_id)
    if not catalog:
        print("error: no catalog cache; run `python3 -m reinvent26 sessions` first", file=sys.stderr)
        return 2
    try:
        sched = api.get_schedule(event_id, token)
    except api.EventsError as e:
        print(f"error: schedule read failed: {e}", file=sys.stderr)
        return 1
    items = cli._confirmed_items(sched, catalog)
    node = sched.get("schedule", {}) if isinstance(sched, dict) else {}
    rids = set(r if isinstance(r, str) else r.get("sessionId") for r in node.get("reserved", []))
    held = [s for s in items if s.get("sessionId") in rids or s.get("code") in rids]
    config = mapper._load_config()
    text = render_findme(_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d"),
                         held, day_gaps(held), talk_topics(items, config), day)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"# wrote {out}", file=sys.stderr)
    else:
        print(text)
    return 0


def main(argv=None) -> int:
    """Argparse entry point: `reinvent26 find-me <event_id> [--day N]`."""
    parser = argparse.ArgumentParser(prog="reinvent26 find-me",
                                     description="render a shareable find-bryan page from the live schedule")
    parser.add_argument("event_id", nargs="?", default=EVENT_ID)
    parser.add_argument("--day", type=int, default=None, help="event day number (1-5); picks the visitor question")
    parser.add_argument("--out", default=None, help="write to a file instead of stdout")
    args = parser.parse_args(argv)
    return run(args.event_id, args.day, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
