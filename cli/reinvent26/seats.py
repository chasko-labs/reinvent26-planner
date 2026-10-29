"""Seat availability sweep: GetSession is the only call that returns seatAvailability.

Writes .cache/<eventId>/seats.json ({fetched_at, event, seats: {code: state}}).
Bounded concurrency; read_with_retry already backs off on 429.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from reinvent26 import api

OPEN = {"available", "limited", "veryLimited"}


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sweep(event_id: str, token: str, catalog: list, workers: int = 6, reservable_only: bool = True) -> dict:
    targets = [s for s in catalog if s.get("sessionId") and (s.get("isReservable") or not reservable_only)]

    def one(s):
        try:
            got = api.get_session(event_id, s["sessionId"], token=token)
            return s.get("abbreviation"), (got.get("session") or got).get("seatAvailability")
        except api.EventsError as e:
            return s.get("abbreviation"), f"error:{e.status if hasattr(e, 'status') else 'http'}"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(pool.map(one, targets))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="reinvent26 seats", description="sweep seat availability into .cache")
    p.add_argument("--event", default="reinvent2026")
    p.add_argument("--catalog", default=None)
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args(argv)
    root = _repo_root()
    cat_path = args.catalog or os.path.join(root, ".cache", args.event, "catalog.json")
    catalog = json.load(open(cat_path, encoding="utf-8"))
    from reinvent26.cli import _token  # stored login token, refreshed when expired
    token = _token(argparse.Namespace(token=None))
    t0 = time.time()
    seats = sweep(args.event, token, catalog, workers=args.workers)
    out = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": args.event, "seats": seats}
    out_path = os.path.join(root, ".cache", args.event, "seats.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    n_open = sum(1 for v in seats.values() if v in OPEN)
    print(f"{len(seats)} reservable sessions in {time.time() - t0:.0f}s, {n_open} with open seats -> {out_path}")
