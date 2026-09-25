"""cli entry point: python -m reinvent26 <command>."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinvent26 import api, schedule, cache, seeds, inventory


def _token(args) -> str | None:
    return args.token or os.environ.get("EVENTS_ACCESS_TOKEN")


def cmd_events(args):
    events = api.list_events(include_past=args.include_past)
    print(json.dumps(events, indent=2))


def _fetch_sessions(args, include_abstracts: bool = False) -> list:
    """Full catalog fetch, saving to cache unless --cached was given."""
    sessions = schedule.normalize_sessions(
        list(
            api.iter_sessions(
                args.event_id, token=_token(args),
                include_abstracts=include_abstracts,
            )
        )
    )
    if not getattr(args, "cached", False):
        path = cache.save_cached_sessions(args.event_id, sessions)
        print(f"# cached {len(sessions)} sessions to {path}", file=sys.stderr)
    return sessions


def _cached_sessions(args) -> list:
    sessions = cache.load_cached_sessions(args.event_id)
    if sessions is None:
        print(
            f"error: no cache for {args.event_id} at "
            f"{cache.cache_file(args.event_id)}; run without --cached "
            "or with --refresh first",
            file=sys.stderr,
        )
        raise SystemExit(2)
    print(f"# using cached catalog ({len(sessions)} sessions, no network)",
          file=sys.stderr)
    return schedule.normalize_sessions(sessions)


def cmd_sessions(args):
    if args.cached and args.refresh:
        print("error: --cached and --refresh conflict", file=sys.stderr)
        raise SystemExit(2)
    if args.cached:
        sessions = _cached_sessions(args)
    else:
        sessions = _fetch_sessions(args, include_abstracts=args.abstracts)
    count = 0
    for s in sessions:
        print(schedule.summarize(s))
        count += 1
        if args.limit and count >= args.limit:
            break
    print(f"# {count} sessions listed (paginated until no nextToken)", file=sys.stderr)


def _apply_time_filters(items: list, args) -> list:
    if args.not_before or args.not_after or args.lunch:
        try:
            return schedule.filter_by_time(
                items,
                not_before=args.not_before,
                not_after=args.not_after,
                lunch=args.lunch,
            )
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            raise SystemExit(2)
    return items


def _resolve_topics(args) -> list:
    """Explicit --topics wins; otherwise blog-aware seeds; --reseed regenerates."""
    if args.topics:
        return [k.strip() for k in args.topics.split(",") if k.strip()]
    if args.reseed:
        topics = seeds.reseed()
        print(f"# reseeded {len(topics)} topics from {seeds.posts_root()}",
              file=sys.stderr)
        return topics
    topics = seeds.load_seeds()
    if topics:
        print(f"# using seed topics from {seeds.seed_path()}", file=sys.stderr)
        return topics
    print("error: no --topics given and no seed file; run with --reseed to "
          f"derive seeds from {seeds.posts_root()}", file=sys.stderr)
    raise SystemExit(2)


def cmd_shortlist(args):
    keywords = _resolve_topics(args)
    exclude = args.exclude.split(",") if args.exclude else None
    if args.cached and args.refresh:
        print("error: --cached and --refresh conflict", file=sys.stderr)
        raise SystemExit(2)
    if args.cached:
        sessions = _cached_sessions(args)
        with open(cache.cache_file(args.event_id), "rb") as fh:
            raw = fh.read()
        levels = [args.level] if args.level and len(args.level) >= 3 else []
        pre = cache.rust_prefilter(raw, topics=keywords, levels=levels, day=args.day)
        if pre is not None:
            print(f"# rust pre-filter: {len(pre)} of {len(sessions)} kept",
                  file=sys.stderr)
            sessions = pre
        else:
            print("# rust filter binary absent: python fallback", file=sys.stderr)
    else:
        sessions = _fetch_sessions(args)
    sessions = schedule.filter_by_day(sessions, args.day)
    sessions = _apply_time_filters(sessions, args)
    if args.offbeat:
        pick = schedule.find_offbeat(sessions, keywords, exclude=exclude)
        if pick is None:
            print("# offbeat: every session matches your topics", file=sys.stderr)
            return
        if args.abstracts:
            full = api.get_session(
                args.event_id, pick.get("sessionId", ""), token=_token(args)
            )
            print(json.dumps(full, indent=2))
        else:
            print(schedule.summarize(pick))
        return
    ranked = schedule.match_topics(sessions, keywords, exclude=exclude)
    if args.level:
        ranked = [s for s in ranked if str(s.get("level", "")).startswith(args.level)]
    for s in ranked[: args.top]:
        if args.abstracts:
            full = api.get_session(
                args.event_id, s.get("sessionId", ""), token=_token(args)
            )
            print(json.dumps(full, indent=2))
        else:
            print(schedule.summarize(s))


def cmd_schedule(args):
    token = _token(args)
    sched = api.get_schedule(args.event_id, token)
    items = _confirmed_items(sched, _catalog_for_confirm(args.event_id, token))
    for i in items:
        print(schedule.summarize(i))
    clashes = schedule.find_clashes(items)
    if clashes:
        print("# double bookings:", file=sys.stderr)
        for a, b in clashes:
            print(
                f"# clash: {a.get('code', a.get('sessionId'))} x "
                f"{b.get('code', b.get('sessionId'))}",
                file=sys.stderr,
            )
    else:
        print("# no double bookings", file=sys.stderr)


def _schedule_items(sched) -> list:
    if isinstance(sched, list):
        return sched
    if not isinstance(sched, dict):
        return []
    items = sched.get("items") or sched.get("sessions") or []
    if items:
        return items if isinstance(items, list) else []
    node = sched.get("schedule")
    if isinstance(node, list):
        return node
    return []


def _parse_window(spec: str) -> dict:
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"window must be 'START,END': {spec!r}")
    start, end = parts
    try:
        if not schedule._parse(start) < schedule._parse(end):
            raise ValueError("window start must be before window end")
    except ValueError:
        raise ValueError(f"window must use ISO timestamps 'START,END': {spec!r}")
    return {"start": start, "end": end}


def cmd_slots(args):
    windows = [_parse_window(w) for w in args.window]
    sessions = schedule.normalize_sessions(
        list(
            api.iter_sessions(args.event_id, token=_token(args),
                              include_abstracts=False)
        )
    )
    sessions = _apply_time_filters(sessions, args)
    scheduled: list = []
    if _token(args):
        try:
            scheduled = _confirmed_items(
                api.get_schedule(args.event_id, _token(args)), sessions)
        except api.EventsError as e:
            print(f"# schedule read failed ({e}); clash check skipped", file=sys.stderr)
    else:
        print("# no token: clash check against live schedule skipped", file=sys.stderr)
    fitting = schedule.find_open_slots(sessions, windows, scheduled)
    for s in fitting:
        line = schedule.summarize(s)
        if s.get("venue"):
            line += f" | {s.get('venue')}"
        print(line)
    print(
        f"# {len(fitting)} sessions fit fully inside the given windows "
        "with no clash",
        file=sys.stderr,
    )


def _catalog_for_confirm(event_id: str, token: str | None) -> list:
    cached = cache.load_cached_sessions(event_id)
    if cached is not None:
        return schedule.normalize_sessions(cached)
    return schedule.normalize_sessions(
        list(api.iter_sessions(event_id, token=token, include_abstracts=False)))


def _confirmed_items(sched, catalog: list) -> list:
    """Resolve a GetSchedule payload to normalized session dicts.

    The live shape nests id strings under schedule.favorites/reserved
    plus personal-time objects under schedule.personalTime; ids resolve
    against the catalog, unknown ids stay as bare timeless entries.
    """
    node = sched.get("schedule") if isinstance(sched, dict) else None
    if isinstance(node, dict):
        by_id = {s.get("sessionId"): s for s in catalog
                 if isinstance(s, dict) and s.get("sessionId")}
        items = []
        for sid in list(node.get("favorites") or []) + \
                list(node.get("reserved") or []):
            if isinstance(sid, dict):
                items.append(sid)
            else:
                items.append(by_id.get(sid) or {"sessionId": sid})
        for entry in node.get("personalTime") or []:
            if isinstance(entry, dict):
                items.append(entry)
        return schedule.normalize_sessions(items)
    return schedule.normalize_sessions(_schedule_items(sched))


def cmd_stack_pick(args):
    """Stack-aware picker end to end: live resources map to catalog keywords."""
    if args.resources_json:
        resources = inventory.load_resources_file(args.resources_json)
        source = f"file:{args.resources_json}"
    else:
        resources = inventory.fetch_via_aws_cli(args.profile, args.region)
        source = f"aws_cli:profile={args.profile}"
    keywords = schedule.stack_keywords(resources)
    print(f"# stack source: {source} ({len(resources)} resources)",
          file=sys.stderr)
    print(f"# keywords: {', '.join(keywords) if keywords else '(none mapped)'}",
          file=sys.stderr)
    for rtype, count in inventory.summarize_inventory(resources)[:10]:
        print(f"# inventory: {rtype} x{count}", file=sys.stderr)
    if not keywords:
        print("# no keywords mapped from live stack; aborting", file=sys.stderr)
        raise SystemExit(2)
    sessions = _fetch_sessions(args)
    ranked = schedule.match_topics(
        sessions, keywords, exclude=args.exclude.split(",") if args.exclude else None
    )
    if args.level:
        ranked = [s for s in ranked if str(s.get("level", "")).startswith(args.level)]
    picks = ranked[: args.top]
    for s in picks:
        print(schedule.summarize(s))
    if args.favorite and picks:
        ids = [s.get("sessionId", "") for s in picks if s.get("sessionId")]
        resps = api.favorite_sessions(args.event_id, _token(args), ids)
        print(json.dumps(resps, indent=2))
        have = {i.get("sessionId") for i in
                _confirmed_items(api.get_schedule(args.event_id, _token(args)),
                                 sessions)
                if isinstance(i, dict)}
        missing = [i for i in ids if i not in have]
        print(f"# event {args.event_id}: favorited "
              f"{len(ids) - len(missing)}/{len(ids)} confirmed by GetSchedule",
              file=sys.stderr)
        if missing:
            print(f"# unconfirmed: {', '.join(missing)}", file=sys.stderr)
    else:
        print("# confirm writes with: schedule command "
              "(GetSchedule is source of truth)")


def cmd_favorite(args):
    ids = [i.strip() for i in args.session_ids.split(",") if i.strip()]
    resps = api.favorite_sessions(args.event_id, _token(args), ids)
    print(json.dumps(resps, indent=2))
    print("# confirm with: schedule command (GetSchedule is source of truth)")


def cmd_reserve(args):
    ids = [i.strip() for i in args.session_ids.split(",") if i.strip()]
    try:
        resps = api.reserve_sessions(args.event_id, _token(args), ids)
    except api.EventsError as e:
        if e.status == 409:
            print(
                "# 409: reserved seating not open yet (api opens 8 Oct 2026). "
                "favorites work now; retry after reopen.",
                file=sys.stderr,
            )
            raise SystemExit(3)
        raise
    print(json.dumps(resps, indent=2))
    print("# per-session results above; confirm with schedule command")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="reinvent26", description="reinvent 2026 catalog planner")
    p.add_argument("--token", default=None, help="access token (or EVENTS_ACCESS_TOKEN)")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("events", help="list current/upcoming events")
    e.add_argument("--include-past", action="store_true")
    e.set_defaults(fn=cmd_events)

    s = sub.add_parser("sessions", help="list catalog pages until no nextToken")
    s.add_argument("event_id")
    s.add_argument("--abstracts", action="store_true")
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--cached", action="store_true",
                   help="read .cache/<eventId>/sessions.json, no network")
    s.add_argument("--refresh", action="store_true",
                   help="fetch live and overwrite the cache")
    s.set_defaults(fn=cmd_sessions)

    sl = sub.add_parser("shortlist", help="rank sessions by topic keywords")
    sl.add_argument("event_id")
    sl.add_argument("--topics", default="",
                    help="comma list, e.g. agents,mcp,bedrock (default: seed file)")
    sl.add_argument("--reseed", action="store_true",
                    help="regenerate seed topics from ~/writing and save")
    sl.add_argument("--exclude", default="")
    sl.add_argument("--level", default="", help="e.g. 300 or 400")
    sl.add_argument("--top", type=int, default=20)
    sl.add_argument("--abstracts", action="store_true")
    sl.add_argument("--not-before", default="", metavar="HH:MM",
                    help="drop sessions starting before this daily time")
    sl.add_argument("--not-after", default="", metavar="HH:MM",
                    help="drop sessions starting after this daily time")
    sl.add_argument("--lunch", default="", metavar="HH:MM-HH:MM",
                    help="block out lunch, e.g. --lunch 12:00-13:00")
    sl.add_argument("--offbeat", action="store_true",
                    help="pick exactly one session unrelated to --topics")
    sl.add_argument("--day", default="", metavar="YYYY-MM-DD",
                    help="only sessions starting that day")
    sl.add_argument("--cached", action="store_true",
                    help="filter .cache/<eventId>/sessions.json via rust "
                    "pre-filter when built, no network")
    sl.add_argument("--refresh", action="store_true",
                    help="fetch live and overwrite the cache")
    sl.set_defaults(fn=cmd_shortlist)

    sc = sub.add_parser("schedule", help="show schedule plus double bookings")
    sc.add_argument("event_id")
    sc.set_defaults(fn=cmd_schedule)

    slt = sub.add_parser("slots", help="list sessions fitting free windows with no clash")
    slt.add_argument("event_id")
    slt.add_argument(
        "--window",
        action="append",
        required=True,
        metavar="START,END",
        help="free window as ISO timestamps, e.g. --window 2026-12-01T13:00:00,2026-12-01T16:00:00 (repeatable)",
    )
    slt.add_argument("--not-before", default="", metavar="HH:MM",
                     help="drop sessions starting before this daily time")
    slt.add_argument("--not-after", default="", metavar="HH:MM",
                     help="drop sessions starting after this daily time")
    slt.add_argument("--lunch", default="", metavar="HH:MM-HH:MM",
                     help="block out lunch, e.g. --lunch 12:00-13:00")
    slt.set_defaults(fn=cmd_slots)

    f = sub.add_parser("favorite", help="favorite up to 10 session ids per call")
    f.add_argument("event_id")
    f.add_argument("session_ids", help="comma separated session ids")
    f.set_defaults(fn=cmd_favorite)

    r = sub.add_parser("reserve", help="reserve seats (api opens 8 Oct 2026)")
    r.add_argument("event_id")
    r.add_argument("session_ids", help="comma separated session ids")
    r.set_defaults(fn=cmd_reserve)

    sp = sub.add_parser("stack-pick", help="stack-aware shortlist from live resources")
    sp.add_argument("event_id")
    sp.add_argument("--profile", default="",
                    help="explicit aws cli profile for read-only inventory")
    sp.add_argument("--resources-json", default="",
                    help="cached get-resources json (offline alternative)")
    sp.add_argument("--region", default=None)
    sp.add_argument("--exclude", default="")
    sp.add_argument("--level", default="")
    sp.add_argument("--top", type=int, default=20)
    sp.add_argument("--favorite", action="store_true",
                    help="favorite picks, then confirm with GetSchedule")
    sp.set_defaults(fn=cmd_stack_pick)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
    except api.EventsError as e:
        print(f"error: {e}", file=sys.stderr)
        if e.status == 403:
            print("# 403 with body: not registered for this event; register on the reinvent site first", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
