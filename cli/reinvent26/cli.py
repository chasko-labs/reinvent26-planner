"""cli entry point: python -m reinvent26 <command>."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinvent26 import api, schedule


def _token(args) -> str | None:
    return args.token or os.environ.get("EVENTS_ACCESS_TOKEN")


def cmd_events(args):
    events = api.list_events(include_past=args.include_past)
    print(json.dumps(events, indent=2))


def cmd_sessions(args):
    count = 0
    for s in api.iter_sessions(
        args.event_id,
        token=_token(args),
        include_abstracts=args.abstracts,
    ):
        print(schedule.summarize(s))
        count += 1
        if args.limit and count >= args.limit:
            break
    print(f"# {count} sessions listed (paginated until no nextToken)", file=sys.stderr)


def cmd_shortlist(args):
    keywords = [k.strip() for k in args.topics.split(",") if k.strip()]
    sessions = list(
        api.iter_sessions(args.event_id, token=_token(args), include_abstracts=False)
    )
    ranked = schedule.match_topics(
        sessions, keywords, exclude=args.exclude.split(",") if args.exclude else None
    )
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
    sched = api.get_schedule(args.event_id, _token(args))
    items = (
        sched.get("items")
        or sched.get("sessions")
        or sched.get("schedule")
        or (sched if isinstance(sched, list) else [])
    )
    for i in items:
        print(schedule.summarize(i))
    clashes = schedule.find_clashes(items if isinstance(items, list) else [])
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
    s.set_defaults(fn=cmd_sessions)

    sl = sub.add_parser("shortlist", help="rank sessions by topic keywords")
    sl.add_argument("event_id")
    sl.add_argument("--topics", required=True, help="comma list, e.g. agents,mcp,bedrock")
    sl.add_argument("--exclude", default="")
    sl.add_argument("--level", default="", help="e.g. 300 or 400")
    sl.add_argument("--top", type=int, default=20)
    sl.add_argument("--abstracts", action="store_true")
    sl.set_defaults(fn=cmd_shortlist)

    sc = sub.add_parser("schedule", help="show schedule plus double bookings")
    sc.add_argument("event_id")
    sc.set_defaults(fn=cmd_schedule)

    f = sub.add_parser("favorite", help="favorite up to 10 session ids per call")
    f.add_argument("event_id")
    f.add_argument("session_ids", help="comma separated session ids")
    f.set_defaults(fn=cmd_favorite)

    r = sub.add_parser("reserve", help="reserve seats (api opens 8 Oct 2026)")
    r.add_argument("event_id")
    r.add_argument("session_ids", help="comma separated session ids")
    r.set_defaults(fn=cmd_reserve)

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
