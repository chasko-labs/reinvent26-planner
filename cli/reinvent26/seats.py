"""Seat availability sweep: GetSession is the only call that returns seatAvailability.

Reads catalog from .cache/<eventId>/catalog.json, writes
.cache/<eventId>/seats.json with seatAvailability by session abbreviation.

Args:
    event_id: re:Invent event identifier
    token: AWS Events API access token
    catalog: list of session dicts from events API
    workers: thread pool size for concurrent GetSession calls
    reservable_only: filter out walk-up-only sessions

Returns:
    dict mapping session abbreviation to seatAvailability string

Side effects:
    Writes .cache/<eventId>/seats.json with {fetched_at, event, seats}

Failure modes:
    api.EventsError: GetSession call failed; recorded as "error:<status>"
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
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root from cli/reinvent26/


def sweep(event_id: str, token: str, catalog: list, workers: int = 6, reservable_only: bool = True) -> dict:
    """Find reservable sessions and query live seat availability via GetSession."""
    targets = [session for session in catalog if session.get("sessionId") and (session.get("isReservable") or not reservable_only)]

    def one(session: dict) -> tuple:
        """Query GetSession for one session's seat availability."""
        try:
            got = api.get_session(event_id, session["sessionId"], token=token)
            return session.get("abbreviation"), (got.get("session") or got).get("seatAvailability")
        except api.EventsError as e:
            return session.get("abbreviation"), f"error:{e.status if hasattr(e, 'status') else 'http'}"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(pool.map(one, targets))


def main(argv=None) -> None:
    """Sweep seat availability and write .cache/<eventId>/seats.json."""
    parser = argparse.ArgumentParser(prog="reinvent26 seats", description="sweep seat availability into .cache")
    parser.add_argument("--event", default="reinvent2026", help="event id (default: reinvent2026)")
    parser.add_argument("--catalog", default=None, help="catalog JSON path (default: .cache/<event>/catalog.json)")
    parser.add_argument("--workers", type=int, default=6, help="thread pool size for concurrent GetSession calls")
    args = parser.parse_args(argv)
    root = _repo_root()
    catalog_path = args.catalog or os.path.join(root, ".cache", args.event, "catalog.json")
    catalog = json.load(open(catalog_path, encoding="utf-8"))
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
