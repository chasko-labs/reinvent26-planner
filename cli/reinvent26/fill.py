"""Gap filler: book open seats into the free windows of the live schedule.

Run on demand or daily (see docs/daily-fill.md). Steps:
  1. read the live schedule (reserved seats are fixed points)
  2. find reservable catalog sessions that fit between held seats under the venue-gap rules
  3. live-check seatAvailability only for those candidates (GetSession is the only source)
  4. book in priority order (format, then topic), re-checking fit after each booking
Fails fast: no token, no catalog, or a slow probe stops the run before any long work.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from reinvent26 import api
from reinvent26 import mapper

EVENT = "reinvent2026"
OPEN = {"available", "limited", "veryLimited"}


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ssm_token() -> str | None:
    """Access token via bin/awsevents-mcp-refresh (ssm-backed, refreshes when expired)."""
    import importlib.machinery
    import importlib.util
    path = os.path.join(repo_root(), "bin", "awsevents-mcp-refresh")
    loader = importlib.machinery.SourceFileLoader("awsevents_refresh", path)
    spec = importlib.util.spec_from_loader("awsevents_refresh", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod.get_valid_access_token()


def window(s: dict):
    return mapper._when(s)


def fits(cand: dict, held: list, config: dict) -> bool:
    """True when cand overlaps nothing held and respects the venue gap on both sides."""
    a, b = cand["_start"], cand["_end"]
    for h in held:
        if h["_start"].date() != a.date():
            continue
        if a < h["_end"] and h["_start"] < b:
            return False
        if b <= h["_start"] and not mapper._compatible(cand, h, config):
            return False
        if h["_end"] <= a and not mapper._compatible(h, cand, config):
            return False
    return True


def priority(s: dict, config: dict) -> float:
    tw = config.get("type_weight", {})
    topic_weight = config.get("topic_weight", {})
    core, rel = mapper._tag(s, config.get("topics", []))
    w = tw.get(s.get("type", ""), tw.get("_default", 5.0))
    w += (max(topic_weight.get(t, 10.0) for t in core) * 0.5) if core else (2.0 if rel else 0.0)
    return w + (s["_end"] - s["_start"]).seconds / 7200


def candidates(catalog: list, held: list, held_bases: set, config: dict) -> list:
    out = []
    for s in catalog:
        if not s.get("isReservable") or s.get("isAllDaySession") or not s.get("venue"):
            continue
        if mapper._base(s.get("abbreviation", "")) in held_bases:
            continue  # already hold a run of this session
        if mapper._is_bedrock_excluded(s, config) or mapper._is_frontier_excluded(s, config)[0]:
            continue
        w = window(s)
        if not w:
            continue
        s = dict(s, _start=w[0], _end=w[1])
        if fits(s, held, config):
            out.append(s)
    return out


def live_seats(token: str, cands: list, workers: int) -> dict:
    def one(s):
        try:
            got = api.get_session(EVENT, s["sessionId"], token=token)
            return s["sessionId"], (got.get("session") or got).get("seatAvailability")
        except api.EventsError:
            return s["sessionId"], None
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(pool.map(one, cands))


def plan_days(pool: list, held_ids: set, config: dict) -> list:
    """Max reserved minutes per day (weighted interval scheduling); format breaks ties, held seats resist churn.

    One run per session base across the week, earlier days first.
    """
    tw = config.get("type_weight", {})
    chosen, taken = [], set()
    for day in sorted({s["_start"].date() for s in pool}):
        cand = sorted([s for s in pool if s["_start"].date() == day and mapper._base(s["abbreviation"]) not in taken],
                      key=lambda s: s["_end"])
        if not cand:
            continue

        def val(s):
            # sessions first (as many events as possible), then reserved minutes, then format, then churn resistance
            mins = (s["_end"] - s["_start"]).seconds / 60
            fmt = tw.get(s.get("type", ""), tw.get("_default", 5.0))
            return 10000 + mins * 20 + fmt * 50 + (300 if s["sessionId"] in held_ids else 0)

        best, prev = [0.0] * len(cand), [-1] * len(cand)
        for i, s in enumerate(cand):
            best[i] = val(s)
            for j in range(i):
                if mapper._compatible(cand[j], s, config) and best[j] + val(s) > best[i]:
                    best[i], prev[i] = best[j] + val(s), j
        i = max(range(len(cand)), key=lambda k: best[k])
        picks = []
        while i != -1:
            picks.append(cand[i])
            i = prev[i]
        seen = set()
        for s in reversed(picks):
            b = mapper._base(s["abbreviation"])
            if b not in seen:
                seen.add(b)
                chosen.append(s)
        taken |= seen
    return chosen


def run(dry_run: bool, workers: int, max_checks: int) -> int:
    root = repo_root()
    config = mapper._load_config()
    cat_path = os.path.join(root, ".cache", EVENT, "catalog.json")
    if not os.path.exists(cat_path):
        print(f"fail: no catalog at {cat_path}; pull it first", file=sys.stderr)
        return 2
    token = ssm_token()
    if not token:
        print("fail: no valid token; run bin/awsevents-mcp-login (ssh tunnel from the browser machine)", file=sys.stderr)
        return 2

    t0 = time.time()
    sched = api.get_schedule(EVENT, token)
    print(f"schedule read in {time.time() - t0:.1f}s")
    catalog = json.load(open(cat_path, encoding="utf-8"))
    byid = {s["sessionId"]: s for s in catalog}
    held = []
    for sid in sched["schedule"].get("reserved", []):
        s = byid.get(sid)
        w = window(s) if s else None
        if w:
            held.append(dict(s, _start=w[0], _end=w[1]))
    held_bases = {mapper._base(h["abbreviation"]) for h in held}
    print(f"held seats: {len(held)}")

    cands = candidates(catalog, held, held_bases, config)
    cands.sort(key=lambda s: priority(s, config), reverse=True)
    cands = cands[:max_checks]
    print(f"candidates that fit a free window: {len(cands)} (checking live seats)")
    if not cands:
        return 0

    t0 = time.time()
    seats = live_seats(token, cands[:12], workers)  # probe first; bail if the api is slow today
    probe = time.time() - t0
    if probe > 30:
        print(f"fail: 12-session probe took {probe:.0f}s; try later", file=sys.stderr)
        return 3
    seats.update(live_seats(token, cands[12:], workers))
    open_c = [s for s in cands if seats.get(s["sessionId"]) in OPEN]
    print(f"open seats among fitting candidates: {len(open_c)} (checked in {time.time() - t0:.0f}s)")

    booked = []
    for s in open_c:
        if not fits(s, held, config) or mapper._base(s["abbreviation"]) in held_bases:
            continue  # an earlier booking this run took the window
        label = f"{s['_start']:%a %m-%d %H:%M} {s['venue']} {s['type']} {s['abbreviation']} | {s['title'][:60]}"
        if dry_run:
            print(f"would book: {label}")
            held.append(s)
            held_bases.add(mapper._base(s["abbreviation"]))
            continue
        res = api.reserve_sessions(EVENT, token, [s["sessionId"]])
        ok = any(s["sessionId"] in b["result"].get("successful", []) for b in res)
        codes = [f["code"] for b in res for f in b["result"].get("failed", [])]
        if not ok and codes == ["other"]:
            res = api.reserve_sessions(EVENT, token, [s["sessionId"]])
            ok = any(s["sessionId"] in b["result"].get("successful", []) for b in res)
            codes = [f["code"] for b in res for f in b["result"].get("failed", [])]
        print(("booked: " if ok else f"skipped ({','.join(codes)}): ") + label)
        if ok:
            held.append(s)
            held_bases.add(mapper._base(s["abbreviation"]))
            booked.append(s["abbreviation"])

    final = api.get_schedule(EVENT, token)
    snap = dict(final, fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(os.path.join(root, ".cache", EVENT, "schedule.json"), "w", encoding="utf-8") as fh:
        json.dump(snap, fh, indent=1)
    print(f"done: booked {len(booked)} {booked}; schedule now holds {len(final['schedule'].get('reserved', []))} reserved")
    return 0


def _conflicts(s: dict, held: list, config: dict) -> list:
    return [h for h in held if h["_start"].date() == s["_start"].date() and not fits(s, [h], config)]


def rebalance(dry_run: bool, workers: int) -> int:
    """Re-plan the week over held seats plus swept open seats, then swap toward more reserved time."""
    root = repo_root()
    config = mapper._load_config()
    token = ssm_token()
    if not token:
        print("fail: no valid token; run bin/awsevents-mcp-login", file=sys.stderr)
        return 2
    catalog = json.load(open(os.path.join(root, ".cache", EVENT, "catalog.json"), encoding="utf-8"))
    sweep_path = os.path.join(root, ".cache", EVENT, "seats-sweep.json")
    seats = json.load(open(sweep_path, encoding="utf-8")).get("seats", {})
    if len(seats) < 1000:
        print(f"fail: seat sweep incomplete ({len(seats)} sessions); finish the sweep first", file=sys.stderr)
        return 2
    byid = {s["sessionId"]: s for s in catalog}
    held_ids = set(api.get_schedule(EVENT, token)["schedule"].get("reserved", []))

    pool = []
    for s in catalog:
        sid = s.get("sessionId")
        bookable = s.get("isReservable") and seats.get(s.get("abbreviation")) in OPEN
        if sid not in held_ids and not bookable:
            continue
        if sid not in held_ids and (mapper._is_bedrock_excluded(s, config) or mapper._is_frontier_excluded(s, config)[0]):
            continue
        w = window(s)
        if not w or s.get("isAllDaySession") or not s.get("venue"):
            continue
        pool.append(dict(s, _start=w[0], _end=w[1]))

    target = plan_days(pool, held_ids, config)
    target_ids = {s["sessionId"] for s in target}
    held = [s for s in pool if s["sessionId"] in held_ids]
    mins = lambda xs: sum((s["_end"] - s["_start"]).seconds // 60 for s in xs)
    print(f"held: {len(held)} seats, {mins(held)} min. target: {len(target)} seats, {mins(target)} min")

    adds = sorted([s for s in target if s["sessionId"] not in held_ids], key=lambda s: s["_start"])
    for s in adds:
        label = f"{s['_start']:%a %H:%M} {s['venue']} {s['type']} {s['abbreviation']} | {s['title'][:55]}"
        drop = _conflicts(s, held, config)
        if any(d["sessionId"] in target_ids for d in drop):
            print(f"skip (would drop a target seat): {label}")
            continue
        got = api.get_session(EVENT, s["sessionId"], token=token)
        live = (got.get("session") or got).get("seatAvailability")
        if live not in OPEN:
            print(f"skip (seat gone: {live}): {label}")
            continue
        verb = "would" if dry_run else "now"
        print(f"{verb} book {label}" + (f"  replacing {[d['abbreviation'] for d in drop]}" if drop else ""))
        if dry_run:
            continue
        for d in drop:
            api.cancel_reservation(EVENT, token, d["sessionId"])
        res = api.reserve_sessions(EVENT, token, [s["sessionId"]])
        ok = any(s["sessionId"] in b["result"].get("successful", []) for b in res)
        if not ok:
            res = api.reserve_sessions(EVENT, token, [s["sessionId"]])
            ok = any(s["sessionId"] in b["result"].get("successful", []) for b in res)
        if ok:
            held = [h for h in held if h not in drop] + [s]
        else:
            print(f"  booking failed {json.dumps(res)[:160]}; rebooking {[d['abbreviation'] for d in drop]}")
            if drop:
                api.reserve_sessions(EVENT, token, [d["sessionId"] for d in drop])

    final = api.get_schedule(EVENT, token)
    with open(os.path.join(root, ".cache", EVENT, "schedule.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(final, fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())), fh, indent=1)
    fin = [byid[i] for i in final["schedule"].get("reserved", []) if i in byid]
    total = sum(int((x.get("sessionTime") or {}).get("length") or 0) for x in fin)
    print(f"schedule now: {len(fin)} reserved, {total} min")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="reinvent26 fill", description="book open seats into free windows of the live schedule")
    p.add_argument("--dry-run", action="store_true", help="report what would be booked, book nothing")
    p.add_argument("--rebalance", action="store_true", help="re-plan over held + swept open seats; swap toward more reserved time")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--max-checks", type=int, default=400, help="cap on live seat checks per run")
    args = p.parse_args(argv)
    if args.rebalance:
        return rebalance(args.dry_run, args.workers)
    return run(args.dry_run, args.workers, args.max_checks)


if __name__ == "__main__":
    sys.exit(main())
