"""Daily new-session watcher: diff the live catalog against the cache,
evaluate added sessions with the local model, and write a report plus a
handoff prompt for kiro-cli with the Events MCP server.

Two modes, both read-only against the API (nothing here reserves,
favorites, or writes personal time):

  python3 -m reinvent26 new-sessions reinvent2026            write docs/new-sessions/<date>.md
  python3 -m reinvent26 new-sessions reinvent2026 --dry-run  print the diff, write nothing

Inputs
  .cache/reinvent2026/sessions.json   last snapshot (ListSessions, abstracts optional)
  stored token via reinvent26.auth    python3 -m reinvent26 login, or EVENTS_ACCESS_TOKEN
  local OpenAI-compat endpoint        default http://127.0.0.1:8181/v1; when it is
                                      unreachable the report still runs on the
                                      deterministic topic-tag fallback

Side effects (unless --dry-run)
  overwrites .cache/<event>/sessions.json with the live catalog
  writes .cache/<event>/seen.json with first-seen dates per session id
  writes docs/new-sessions/new-sessions-<date>.md (UTC date)

Fails fast
  exit 2: no valid token, or (non-dry-run) no cache and the live fetch
          failed, or the live catalog came back empty (the API has served
          zero sessions before; an empty pull is treated as an outage,
          never as "everything was removed")
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from reinvent26 import api, cache, mapper, rank, schedule

EVENT_ID = "reinvent2026"
OPEN = {"available", "limited", "veryLimited"}
DEFAULT_WORKERS = 6  # GetSession is slow; added sessions are usually a handful
DEFAULT_MAX_CHECKS = 100


def repo_root() -> str:
    """Repository root: this file lives at <root>/cli/reinvent26/newevents.py."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def access_token() -> str | None:
    """Return a valid Events API access token, or None when sign-in is needed."""
    from reinvent26 import auth
    return auth.stored_access_token()


def seen_file(event_id: str) -> str:
    root = repo_root()
    return os.path.join(root, ".cache", event_id, "seen.json")


def load_seen(event_id: str) -> dict:
    try:
        with open(seen_file(event_id), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_seen(event_id: str, seen: dict) -> str:
    path = seen_file(event_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(seen, fh)
    return path


def diff_catalogs(old: list, live: list) -> tuple:
    """Split the live catalog into (added, removed) against the old snapshot.

    Identity is sessionId; rows without one are ignored on both sides.
    """
    old_ids = {s.get("sessionId") for s in old if isinstance(s, dict) and s.get("sessionId")}
    live_ids = {s.get("sessionId") for s in live if isinstance(s, dict) and s.get("sessionId")}
    added = [s for s in live if isinstance(s, dict) and s.get("sessionId") and s.get("sessionId") not in old_ids]
    removed = [s for s in old if isinstance(s, dict) and s.get("sessionId") and s.get("sessionId") not in live_ids]
    key = lambda s: (s.get("startTime") or "", s.get("sessionId") or "")
    return sorted(added, key=key), sorted(removed, key=key)


def parse_session_detail(payload: dict) -> tuple:
    """Pull (seat_availability, abstract, reservable) out of a GetSession payload."""
    node = payload.get("session") if isinstance(payload, dict) else None
    if not isinstance(node, dict):
        node = payload if isinstance(payload, dict) else {}
    return (
        node.get("seatAvailability"),
        str(node.get("abstract") or node.get("description") or ""),
        node.get("isReservable"),
    )


def enrich(event_id: str, token: str, added: list, workers: int, max_checks: int) -> list:
    """GetSession per added session: seat, abstract, reservable flag.

    Bounded by max_checks; entries past the cap keep (None, "", None) and
    the report says so. Never raises for one bad session.
    """
    out = []
    for s in added[:max_checks]:
        try:
            got = api.get_session(event_id, s.get("sessionId", ""), token=token)
            seat, abstract, reservable = parse_session_detail(got)
        except api.EventsError:
            seat, abstract, reservable = None, "", None
        row = dict(s)
        row["_seat"] = seat
        if abstract and not row.get("abstract"):
            row["abstract"] = abstract[:2000]
        row["_reservable"] = reservable if reservable is not None else s.get("isReservable")
        out.append(row)
    for s in added[max_checks:]:
        row = dict(s)
        row["_seat"], row["_reservable"] = None, s.get("isReservable")
        out.append(row)
    return out


def resolve_held(sched: dict, catalog: list) -> list:
    """Resolve a GetSchedule payload to normalized session dicts.

    Mirrors the cli resolution: favorites plus reserved ids resolve against
    the catalog, personal-time entries pass through.
    """
    node = sched.get("schedule") if isinstance(sched, dict) else None
    if not isinstance(node, dict):
        return []
    by_id = {s.get("sessionId"): s for s in catalog
             if isinstance(s, dict) and s.get("sessionId")}
    items = []
    for sid in list(node.get("favorites") or []) + list(node.get("reserved") or []):
        items.append(by_id.get(sid, {"sessionId": sid}) if not isinstance(sid, dict) else sid)
    for entry in node.get("personalTime") or []:
        if isinstance(entry, dict):
            items.append(entry)
    return schedule.normalize_sessions(items)


def _windowed(session: dict) -> dict | None:
    """Copy of a normalized session with _start/_end datetimes, or None.

    fill.with_window reads the raw sessionTime shape; the watcher works on
    normalized startTime/endTime, so windows are attached here and fill.fits
    (which only needs _start/_end plus venue) does the gap math.
    """
    if not session.get("startTime") or not session.get("endTime"):
        return None
    try:
        start = schedule._parse(session["startTime"])
        end = schedule._parse(session["endTime"])
    except ValueError:
        return None
    if not session.get("venue"):
        return None
    return dict(session, _start=start, _end=end)


def evaluate(added: list, config: dict) -> list:
    """Deterministic ordering: core topic matches first, then related, then rest.

    Each row gains _core/_rel topic lists. Stable and unit-testable; the
    local model re-ranks on top of this in run().
    """
    scored = []
    for s in added:
        core, rel = mapper._tag(s, config.get("topics", []))
        row = dict(s)
        row["_core"], row["_rel"] = core, rel
        scored.append(((0 if core else 1, 0 if rel else 1, s.get("startTime") or ""), row))
    scored.sort(key=lambda t: t[0])
    return [row for _, row in scored]


def rank_new(added: list, config: dict, endpoint: str, model: str) -> tuple:
    """Local-model re-rank of added sessions; falls back to evaluate() order.

    Returns (ranked, method) where method is "local-model" or "topic-tags".
    The model only ranks: unknown codes are dropped against the added list.
    """
    if not added:
        return [], "topic-tags"
    topics = [t.get("name", "") for t in config.get("topics", []) if t.get("name")]
    query = ("new re:Invent sessions for an attendee tracking "
             + (", ".join(topics) if topics else "general cloud topics"))
    try:
        ranked = rank.rank_via_model(query, added, endpoint=endpoint, model=model,
                                     top=len(added), timeout=120)
        return ranked, "local-model"
    except Exception as e:  # endpoint down, model disagrees: deterministic path still reports
        print(f"# local model unavailable ({e}); using topic-tag order", file=sys.stderr)
        return evaluate(added, config), "topic-tags"


def opportunities(ranked: list, held: list, config: dict) -> tuple:
    """Split ranked new sessions into (fits, conflicts).

    fits: open seat, survives the exclusion rules, leaves travel gaps.
    conflicts: overlaps a held seat or breaks a venue gap (names the clash).
    Sessions with unknown seats sit in neither; the report lists them as unchecked.
    """
    from reinvent26 import fill as _fill
    held_w = [h for h in (_windowed(s) for s in held) if h]
    fits, conflicts = [], []
    for s in ranked:
        if s.get("_seat") not in OPEN:
            continue
        if _fill.is_excluded_by_rules(s, config):
            continue
        cand = _windowed(s)
        if cand is None:
            continue
        if _fill.fits(cand, held_w, config):
            fits.append(s)
        else:
            clash = [h for h in held_w if not _fill.fits(cand, [h], config)]
            conflicts.append((s, clash[:2]))
    return fits, conflicts


def _code(s: dict) -> str:
    return str(s.get("code") or s.get("abbreviation") or s.get("sessionId") or "?")


def render_report(date: str, event_id: str, added: list, removed: list,
                  fits: list, conflicts: list, unchecked: list,
                  held_count: int, method: str, signals: list | None = None) -> str:
    """Daily markdown report for bryan: what is new, what fits, what clashes."""
    lines = [
        f"# new sessions {date} ({event_id})",
        "",
        f"ranked by {method}; seats live-checked at report time and move fast.",
        f"schedule seats consulted (held plus shortlist): {held_count}.",
        "",
        "## opportunities (open seat, fits your week)",
        "",
    ]
    if fits:
        lines.append("| code | day | time | venue | type | level | seat | topics | title |")
        lines.append("| ---- | --- | ---- | ----- | ---- | ----- | ---- | ------ | ----- |")
        for s in fits:
            core = ",".join(s.get("_core") or [])
            lines.append(
                f"| {_code(s)} | {(s.get('startTime') or '')[:10]} | "
                f"{(s.get('startTime') or '')[11:16]}-{(s.get('endTime') or '')[11:16]} | "
                f"{s.get('venue', '')} | {s.get('type', '')} | {s.get('level', '')} | "
                f"{s.get('_seat', '')} | {core} | {s.get('title', '')} |"
            )
    else:
        lines.append("none. every new session is full, excluded, or clashes.")
    lines += ["", "## launch signals among new sessions", ""]
    if signals:
        for s in signals:
            lines.append(f"- {_code(s)} [{s.get('_sig', '')}] {s.get('_kw', '')} — {s.get('title', '')}")
    else:
        lines.append("none. no added session title or abstract signals a launch.")
    lines += ["", "## conflicts (open seat, clashes with a held seat)", ""]
    if conflicts:
        for s, clash in conflicts:
            names = ", ".join(_code(h) for h in clash) or "held time"
            lines.append(f"- {_code(s)} {s.get('title', '')} — clashes with {names}")
    else:
        lines.append("none.")
    lines += ["", "## new but unchecked (seat unknown, re-run to refresh)", ""]
    if unchecked:
        for s in unchecked:
            lines.append(f"- {_code(s)} {s.get('title', '')}")
    else:
        lines.append("none.")
    lines += ["", "## removed from the catalog", ""]
    if removed:
        for s in removed:
            lines.append(f"- {_code(s)} {s.get('title', '')}")
    else:
        lines.append("none.")
    lines += ["", "## all added sessions", ""]
    if added:
        for s in added:
            lines.append(f"- {_code(s)} | {s.get('startTime', '')} | "
                         f"{s.get('venue', '')} | seat={s.get('_seat')} | {s.get('title', '')}")
    else:
        lines.append("none. catalog unchanged since the last snapshot.")
    lines += ["", "## handoff to kiro-cli (events mcp)", "",
              "setup once: docs/integrations/kiro-cli.md. then paste:",
              "", "```"]
    lines.append(render_handoff(event_id, fits, conflicts))
    lines.append("```")
    return "\n".join(lines) + "\n"


def render_handoff(event_id: str, fits: list, conflicts: list) -> str:
    """Prompt block for kiro-cli with the AWS Events MCP server configured."""
    lines = [
        f"Event {event_id}. Work only through the AWS Events MCP tools.",
        "First list events and read my schedule (GetSchedule is the source of truth).",
    ]
    if fits:
        ids = ", ".join(s.get("sessionId", "") for s in fits if s.get("sessionId"))
        lines.append(f"Reserve these session ids in order (per-session results matter): {ids}.")
    else:
        lines.append("Reserve nothing new: no fitting open seats in this report.")
    fav = [s.get("sessionId", "") for s, _ in conflicts if s.get("sessionId")]
    if fav:
        lines.append(f"Favorite these for later (do not reserve, they clash): {', '.join(fav)}.")
    for s, clash in conflicts:
        names = ", ".join(_code(h) for h in clash) or "held time"
        lines.append(f"Note why {(s.get('sessionId') or _code(s))} was skipped: clashes with {names}.")
    lines.append("Report every per-session result, then read GetSchedule back and show me the final state.")
    return "\n".join(lines)


def default_out_dir() -> str:
    return os.path.join(repo_root(), "docs", "new-sessions")


def run(event_id: str, dry_run: bool, workers: int, max_checks: int,
        endpoint: str, model: str, out_dir: str | None) -> int:
    """Fetch, diff, enrich, evaluate, report. Returns a process exit code."""
    token = access_token()
    if not token:
        print("error: no valid token; run `python3 -m reinvent26 login` first", file=sys.stderr)
        return 2
    old = cache.load_cached_sessions(event_id)
    try:
        live = schedule.normalize_sessions(
            list(api.iter_sessions(event_id, token=token, include_abstracts=False)))
    except api.EventsError as e:
        print(f"error: live catalog fetch failed: {e}", file=sys.stderr)
        return 1
    if not live:
        print("error: live catalog came back empty; treating as outage, cache untouched",
              file=sys.stderr)
        return 1
    if old is None:
        path = cache.save_cached_sessions(event_id, live)
        print(f"# no cache: recorded baseline of {len(live)} sessions to {path}; "
              "rerun for diffs", file=sys.stderr)
        if dry_run:
            return 0
        old = []
    added, removed = diff_catalogs(old, live)
    print(f"# catalog: {len(live)} live, {len(added)} added, {len(removed)} removed",
          file=sys.stderr)
    config = mapper._load_config()
    enriched = enrich(event_id, token, added, workers, max_checks)
    ranked, method = rank_new(enriched, config, endpoint, model)
    try:
        held = resolve_held(api.get_schedule(event_id, token), live)
    except api.EventsError as e:
        print(f"# schedule read failed ({e}); conflicts skipped", file=sys.stderr)
        held = []
    held_reserved = [h for h in held if h.get("startTime")]
    fits, conflicts = opportunities(ranked, held_reserved, config)
    checked_ids = {id(s) for s in fits} | {id(s) for s, _ in conflicts}
    unchecked = [s for s in ranked if id(s) not in checked_ids]
    signals = mapper.launch_signals(enriched)
    print(f"# launch signals among added: {len(signals)}", file=sys.stderr)
    today = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    report = render_report(today, event_id, ranked, removed, fits, conflicts,
                           unchecked, len(held_reserved), method, signals)
    if dry_run:
        print(report)
        return 0
    cache.save_cached_sessions(event_id, live)
    seen = load_seen(event_id)
    for s in added:
        sid = s.get("sessionId")
        if sid and sid not in seen:
            seen[sid] = today
    save_seen(event_id, seen)
    target_dir = out_dir or default_out_dir()
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, f"new-sessions-{today}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(report)
    print(f"# report: {path} ({len(fits)} opportunities, "
          f"{len(conflicts)} conflicts, {len(removed)} removed)", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    """Argparse entry point: `reinvent26 new-sessions <event_id>`."""
    parser = argparse.ArgumentParser(prog="reinvent26 new-sessions",
                                     description="diff the live catalog, evaluate new sessions, write a daily report")
    parser.add_argument("event_id", nargs="?", default=EVENT_ID)
    parser.add_argument("--dry-run", action="store_true", help="print the report, write nothing")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--max-checks", type=int, default=DEFAULT_MAX_CHECKS,
                        help="cap on live GetSession checks")
    parser.add_argument("--endpoint", default=rank.DEFAULT_ENDPOINT)
    parser.add_argument("--model", default="local")
    parser.add_argument("--out-dir", default=None, help="report directory (default: docs/new-sessions)")
    args = parser.parse_args(argv)
    return run(args.event_id, args.dry_run, args.workers, args.max_checks,
               args.endpoint, args.model, args.out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
