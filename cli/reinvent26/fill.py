"""Seat booker: fill free windows of the live re:Invent schedule with open reserved seats.

Two modes, both run by hand (nothing here schedules itself):

  python3 -m reinvent26 fill              book open seats that fit around the seats you already hold
  python3 -m reinvent26 fill --rebalance  re-plan the whole week over held seats plus swept open seats,
                                          then swap toward the plan (cancel conflicts, book, roll back)
  add --dry-run to either to print the plan and book nothing

Inputs
  .cache/reinvent2026/catalog.json      full catalog snapshot (ListSessions with abstracts)
  .cache/reinvent2026/seats-sweep.json  seatAvailability per session code (rebalance only; from seats.py)
  data/reinvent2026/map-config.json     venue gaps, format weights, topic weights, exclusion rules
  ssm token store                       via bin/awsevents-mcp-refresh (see ssm_token)

Side effects
  POST /reservations and DELETE /reservations/{id} against the live Events API (unless --dry-run)
  writes .cache/reinvent2026/schedule.json with the final GET /schedule response

Fails fast
  exit 2: no catalog, no token, or (rebalance) an incomplete seat sweep
  exit 3: the 12-session availability probe took longer than 30 s (the api is slow; try later)
"""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from reinvent26 import api
from reinvent26 import mapper

EVENT_ID = "reinvent2026"
OPEN = mapper.OPEN_SEATS  # seatAvailability values that mean a reservation can still succeed

# fail-fast probe: check this many sessions first and give up if it is slower than the limit
PROBE_SIZE = 12
PROBE_MAX_SECONDS = 30
DEFAULT_WORKERS = 12  # concurrent GetSession calls; 12 measured ~0.4 s per session with no 429s
DEFAULT_MAX_CHECKS = 400  # cap on live seat checks per fill run

# rebalance objective (plan_days): bryan wants as many reserved events as possible, start to finish.
# session count dominates, then reserved minutes, then format (workshop > chalk talk > breakout),
# and a seat already held wins exact ties so the planner does not churn bookings for nothing
SESSION_COUNT_WEIGHT = 10000
MINUTE_WEIGHT = 20
FORMAT_WEIGHT_SCALE = 50
HELD_SEAT_BONUS = 300

# fill ordering (priority): format first, topic fit as a tie-breaker, duration last
TOPIC_TIE_BREAK_SCALE = 0.5
RELATED_TOPIC_TIE_BREAK = 2.0
DURATION_TIE_BREAK_MINUTES_PER_POINT = 7200 / 60  # 2 hours of duration = 1 point


def repo_root() -> str:
    """Repository root: this file lives at <root>/cli/reinvent26/fill.py."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ssm_token() -> str | None:
    """Return a valid Events API access token from bin/awsevents-mcp-refresh, or None when sign-in is needed.

    The helper is a script without a .py suffix, so it is loaded by path rather than imported.
    """
    helper_path = os.path.join(repo_root(), "bin", "awsevents-mcp-refresh")
    helper_loader = importlib.machinery.SourceFileLoader("awsevents_refresh", helper_path)
    helper_spec = importlib.util.spec_from_loader("awsevents_refresh", helper_loader)
    helper_module = importlib.util.module_from_spec(helper_spec)
    helper_loader.exec_module(helper_module)
    return helper_module.get_valid_access_token()


def window(session: dict):
    """(start, end) datetimes for a session, or None when the catalog has no time yet."""
    return mapper._when(session)


def with_window(session: dict) -> dict | None:
    """Copy of the session with _start/_end attached, or None when it has no usable time slot."""
    session_window = window(session)
    if not session_window or session.get("isAllDaySession") or not session.get("venue"):
        return None
    return dict(session, _start=session_window[0], _end=session_window[1])


def fits(candidate_session: dict, held_sessions: list, config: dict) -> bool:
    """True when the candidate overlaps no held seat and leaves the venue travel gap on both sides.

    Only same-day held seats matter. The gap rule comes from map-config.json: 0 minutes within one
    venue, 30 between strip-cluster venues, 60 to or from mgm grand.
    """
    candidate_start, candidate_end = candidate_session["_start"], candidate_session["_end"]
    for held_session in held_sessions:
        if held_session["_start"].date() != candidate_start.date():
            continue
        overlaps = candidate_start < held_session["_end"] and held_session["_start"] < candidate_end
        if overlaps:
            return False
        candidate_is_before = candidate_end <= held_session["_start"]
        if candidate_is_before and not mapper._compatible(candidate_session, held_session, config):
            return False  # not enough travel time from the candidate to the next held seat
        candidate_is_after = held_session["_end"] <= candidate_start
        if candidate_is_after and not mapper._compatible(held_session, candidate_session, config):
            return False  # not enough travel time from the previous held seat to the candidate
    return True


def priority(session: dict, config: dict) -> float:
    """Booking order for fill: format weight first, then topic fit, then duration as the last tie-breaker."""
    format_weight_by_type = config.get("type_weight", {})
    topic_weight_by_name = config.get("topic_weight", {})
    core_topics, related_topics = mapper._tag(session, config.get("topics", []))
    score = format_weight_by_type.get(session.get("type", ""), format_weight_by_type.get("_default", mapper.DEFAULT_FORMAT_WEIGHT))
    if core_topics:
        score += max(topic_weight_by_name.get(topic, mapper.DEFAULT_TOPIC_WEIGHT) for topic in core_topics) * TOPIC_TIE_BREAK_SCALE
    elif related_topics:
        score += RELATED_TOPIC_TIE_BREAK
    duration_minutes = (session["_end"] - session["_start"]).seconds / 60
    return score + duration_minutes / DURATION_TIE_BREAK_MINUTES_PER_POINT


def is_excluded_by_rules(session: dict, config: dict) -> bool:
    """Bryan's standing exclusions: amazon bedrock (nova excepted) and frontier-model sessions by title."""
    return mapper._is_bedrock_excluded(session, config) or mapper._is_frontier_excluded(session, config)[0]


def candidates(catalog: list, held_sessions: list, held_base_codes: set, config: dict) -> list:
    """Reservable sessions that fit a free window, excluding repeats of held seats and excluded subjects."""
    fitting_sessions = []
    for catalog_session in catalog:
        if not catalog_session.get("isReservable"):
            continue
        if mapper._base(catalog_session.get("abbreviation", "")) in held_base_codes:
            continue  # already hold one run of this session (-R/-R1 repeats share a base code)
        if is_excluded_by_rules(catalog_session, config):
            continue
        timed_session = with_window(catalog_session)
        if timed_session and fits(timed_session, held_sessions, config):
            fitting_sessions.append(timed_session)
    return fitting_sessions


def live_seats(token: str, sessions_to_check: list, workers: int) -> dict:
    """sessionId -> seatAvailability, fetched live. GetSession is the only call that returns this field."""
    def fetch_seat_availability(session: dict) -> tuple:
        try:
            get_session_response = api.get_session(EVENT_ID, session["sessionId"], token=token)
            return session["sessionId"], (get_session_response.get("session") or get_session_response).get("seatAvailability")
        except api.EventsError:
            return session["sessionId"], None  # unknown counts as not bookable this run
    with ThreadPoolExecutor(max_workers=workers) as thread_pool:
        return dict(thread_pool.map(fetch_seat_availability, sessions_to_check))


def reserve_one(token: str, session_id: str) -> tuple:
    """Reserve a single session; retry once when the failure code is 'other' (it cleared on retry before).

    Returns (booking_succeeded, failure_codes).
    """
    failure_codes = []
    for _attempt in range(2):
        reserve_response = api.reserve_sessions(EVENT_ID, token, [session_id])
        booking_succeeded = any(session_id in batch["result"].get("successful", []) for batch in reserve_response)
        if booking_succeeded:
            return True, []
        failure_codes = [failure["code"] for batch in reserve_response for failure in batch["result"].get("failed", [])]
        if failure_codes != ["other"]:
            break  # sessionFull, scheduleConflict, etc. will not change on an immediate retry
    return False, failure_codes


def total_minutes(sessions: list) -> int:
    """Sum of session durations in minutes."""
    return sum((session["_end"] - session["_start"]).seconds // 60 for session in sessions)


def held_sessions_from_schedule(schedule_response: dict, sessions_by_id: dict) -> list:
    """Timed catalog sessions for every reserved id in a GET /schedule response."""
    held_sessions = []
    for reserved_id in schedule_response["schedule"].get("reserved", []):
        catalog_session = sessions_by_id.get(reserved_id)
        timed_session = with_window(catalog_session) if catalog_session else None
        if timed_session:
            held_sessions.append(timed_session)
    return held_sessions


def save_schedule_snapshot(token: str) -> dict:
    """Read GET /schedule and persist it to .cache so the map and interest pages see current bookings."""
    schedule_response = api.get_schedule(EVENT_ID, token)
    snapshot = dict(schedule_response, fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(os.path.join(repo_root(), ".cache", EVENT_ID, "schedule.json"), "w", encoding="utf-8") as snapshot_file:
        json.dump(snapshot, snapshot_file, indent=1)
    return schedule_response


def plan_days(session_pool: list, held_ids: set, config: dict) -> list:
    """Best reserved plan for the week: weighted interval scheduling per day, one run per base code.

    For each day, sessions sorted by end time; best_total[i] is the best plan ending with session i,
    built from the best compatible earlier plan (compatible = no overlap plus the venue travel gap).
    Sorting by end time makes every compatible predecessor appear earlier in the list, so one pass
    fills the table. O(n^2) per day, and n is tens of sessions.
    """
    format_weight_by_type = config.get("type_weight", {})
    chosen_sessions, taken_base_codes = [], set()

    def session_value(session: dict) -> float:
        duration_minutes = (session["_end"] - session["_start"]).seconds / 60
        format_weight = format_weight_by_type.get(session.get("type", ""), format_weight_by_type.get("_default", mapper.DEFAULT_FORMAT_WEIGHT))
        held_bonus = HELD_SEAT_BONUS if session["sessionId"] in held_ids else 0
        return SESSION_COUNT_WEIGHT + duration_minutes * MINUTE_WEIGHT + format_weight * FORMAT_WEIGHT_SCALE + held_bonus

    for plan_day in sorted({session["_start"].date() for session in session_pool}):
        day_sessions = sorted(
            [session for session in session_pool
             if session["_start"].date() == plan_day and mapper._base(session["abbreviation"]) not in taken_base_codes],
            key=lambda session: session["_end"],
        )
        if not day_sessions:
            continue
        best_total = [0.0] * len(day_sessions)
        previous_index = [-1] * len(day_sessions)
        for session_index, session in enumerate(day_sessions):
            best_total[session_index] = session_value(session)
            for earlier_index in range(session_index):
                extended_total = best_total[earlier_index] + session_value(session)
                if mapper._compatible(day_sessions[earlier_index], session, config) and extended_total > best_total[session_index]:
                    best_total[session_index], previous_index[session_index] = extended_total, earlier_index
        # walk back from the best ending session to recover the chosen chain
        chain_index = max(range(len(day_sessions)), key=lambda index: best_total[index])
        picked_sessions = []
        while chain_index != -1:
            picked_sessions.append(day_sessions[chain_index])
            chain_index = previous_index[chain_index]
        seen_base_codes = set()
        for session in reversed(picked_sessions):
            base_code = mapper._base(session["abbreviation"])
            if base_code not in seen_base_codes:  # a day can hold two runs of one session; keep the first
                seen_base_codes.add(base_code)
                chosen_sessions.append(session)
        taken_base_codes |= seen_base_codes
    return chosen_sessions


def run(dry_run: bool, workers: int, max_checks: int) -> int:
    """Fill mode: book open seats into free windows without touching anything already held."""
    config = mapper._load_config()
    catalog_path = os.path.join(repo_root(), ".cache", EVENT_ID, "catalog.json")
    if not os.path.exists(catalog_path):
        print(f"fail: no catalog at {catalog_path}; pull it first", file=sys.stderr)
        return 2
    token = ssm_token()
    if not token:
        print("fail: no valid token; run bin/awsevents-mcp-login (ssh tunnel from the browser machine)", file=sys.stderr)
        return 2

    read_started = time.time()
    schedule_response = api.get_schedule(EVENT_ID, token)
    print(f"schedule read in {time.time() - read_started:.1f}s")
    with open(catalog_path, encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    sessions_by_id = {session["sessionId"]: session for session in catalog}
    held_sessions = held_sessions_from_schedule(schedule_response, sessions_by_id)
    held_base_codes = {mapper._base(session["abbreviation"]) for session in held_sessions}
    print(f"held seats: {len(held_sessions)}")

    fitting_sessions = candidates(catalog, held_sessions, held_base_codes, config)
    fitting_sessions.sort(key=lambda session: priority(session, config), reverse=True)
    fitting_sessions = fitting_sessions[:max_checks]
    print(f"candidates that fit a free window: {len(fitting_sessions)} (checking live seats)")
    if not fitting_sessions:
        return 0

    probe_started = time.time()
    seat_by_session_id = live_seats(token, fitting_sessions[:PROBE_SIZE], workers)
    probe_seconds = time.time() - probe_started
    if probe_seconds > PROBE_MAX_SECONDS:
        print(f"fail: {PROBE_SIZE}-session probe took {probe_seconds:.0f}s; try later", file=sys.stderr)
        return 3
    seat_by_session_id.update(live_seats(token, fitting_sessions[PROBE_SIZE:], workers))
    bookable_sessions = [session for session in fitting_sessions if seat_by_session_id.get(session["sessionId"]) in OPEN]
    print(f"open seats among fitting candidates: {len(bookable_sessions)} (checked in {time.time() - probe_started:.0f}s)")

    booked_codes = []
    for session in bookable_sessions:
        # an earlier booking this run may have taken the window or a run of the same session
        if not fits(session, held_sessions, config) or mapper._base(session["abbreviation"]) in held_base_codes:
            continue
        label = f"{session['_start']:%a %m-%d %H:%M} {session['venue']} {session['type']} {session['abbreviation']} | {session['title'][:60]}"
        if dry_run:
            print(f"would book: {label}")
            booking_succeeded, failure_codes = True, []
        else:
            booking_succeeded, failure_codes = reserve_one(token, session["sessionId"])
            print(("booked: " if booking_succeeded else f"skipped ({','.join(failure_codes)}): ") + label)
        if booking_succeeded:
            held_sessions.append(session)
            held_base_codes.add(mapper._base(session["abbreviation"]))
            booked_codes.append(session["abbreviation"])

    final_schedule = save_schedule_snapshot(token)
    print(f"done: {'would book' if dry_run else 'booked'} {len(booked_codes)} {booked_codes}; "
          f"schedule now holds {len(final_schedule['schedule'].get('reserved', []))} reserved")
    return 0


def _conflicts(candidate_session: dict, held_sessions: list, config: dict) -> list:
    """Held seats that would have to be cancelled for the candidate to fit."""
    return [held_session for held_session in held_sessions
            if held_session["_start"].date() == candidate_session["_start"].date()
            and not fits(candidate_session, [held_session], config)]


def rebalance(dry_run: bool, workers: int) -> int:
    """Rebalance mode: re-plan the week over held seats plus swept open seats, then swap toward the plan.

    Every swap re-checks the new seat live, cancels the conflicting held seats, books the new one,
    and rebooks the cancelled seats when the booking fails.
    """
    config = mapper._load_config()
    token = ssm_token()
    if not token:
        print("fail: no valid token; run bin/awsevents-mcp-login", file=sys.stderr)
        return 2
    cache_dir = os.path.join(repo_root(), ".cache", EVENT_ID)
    with open(os.path.join(cache_dir, "catalog.json"), encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    with open(os.path.join(cache_dir, "seats-sweep.json"), encoding="utf-8") as sweep_file:
        seat_by_code = json.load(sweep_file).get("seats", {})
    if len(seat_by_code) < 1000:
        print(f"fail: seat sweep incomplete ({len(seat_by_code)} sessions); finish the sweep first", file=sys.stderr)
        return 2
    sessions_by_id = {session["sessionId"]: session for session in catalog}
    held_ids = set(api.get_schedule(EVENT_ID, token)["schedule"].get("reserved", []))

    session_pool = []
    for catalog_session in catalog:
        session_id = catalog_session.get("sessionId")
        is_held = session_id in held_ids
        is_bookable = catalog_session.get("isReservable") and seat_by_code.get(catalog_session.get("abbreviation")) in OPEN
        if not (is_held or is_bookable):
            continue
        if not is_held and is_excluded_by_rules(catalog_session, config):
            continue
        timed_session = with_window(catalog_session)
        if timed_session:
            session_pool.append(timed_session)

    target_sessions = plan_days(session_pool, held_ids, config)
    target_ids = {session["sessionId"] for session in target_sessions}
    held_sessions = [session for session in session_pool if session["sessionId"] in held_ids]
    print(f"held: {len(held_sessions)} seats, {total_minutes(held_sessions)} min. "
          f"target: {len(target_sessions)} seats, {total_minutes(target_sessions)} min")

    for new_session in sorted([s for s in target_sessions if s["sessionId"] not in held_ids], key=lambda s: s["_start"]):
        label = f"{new_session['_start']:%a %H:%M} {new_session['venue']} {new_session['type']} {new_session['abbreviation']} | {new_session['title'][:55]}"
        conflicting_held_sessions = _conflicts(new_session, held_sessions, config)
        if any(conflict["sessionId"] in target_ids for conflict in conflicting_held_sessions):
            print(f"skip (would drop a target seat): {label}")
            continue
        live_availability = live_seats(token, [new_session], 1).get(new_session["sessionId"])
        if live_availability not in OPEN:
            print(f"skip (seat gone: {live_availability}): {label}")
            continue
        replacing_note = f"  replacing {[c['abbreviation'] for c in conflicting_held_sessions]}" if conflicting_held_sessions else ""
        print(f"{'would' if dry_run else 'now'} book {label}{replacing_note}")
        if dry_run:
            continue
        for conflict in conflicting_held_sessions:
            api.cancel_reservation(EVENT_ID, token, conflict["sessionId"])
        booking_succeeded, failure_codes = reserve_one(token, new_session["sessionId"])
        if booking_succeeded:
            held_sessions = [held for held in held_sessions if held not in conflicting_held_sessions] + [new_session]
        else:
            print(f"  booking failed ({','.join(failure_codes)}); rebooking {[c['abbreviation'] for c in conflicting_held_sessions]}")
            if conflicting_held_sessions:
                api.reserve_sessions(EVENT_ID, token, [c["sessionId"] for c in conflicting_held_sessions])

    final_schedule = save_schedule_snapshot(token)
    final_reserved_sessions = held_sessions_from_schedule(final_schedule, sessions_by_id)
    print(f"schedule now: {len(final_reserved_sessions)} reserved, {total_minutes(final_reserved_sessions)} min")
    return 0


def main(argv=None) -> int:
    """CLI entry for `reinvent26 fill`; returns the process exit code."""
    argument_parser = argparse.ArgumentParser(prog="reinvent26 fill", description="book open seats into free windows of the live schedule")
    argument_parser.add_argument("--dry-run", action="store_true", help="report what would be booked, book nothing")
    argument_parser.add_argument("--rebalance", action="store_true", help="re-plan over held + swept open seats; swap toward more reserved events")
    argument_parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="concurrent GetSession calls")
    argument_parser.add_argument("--max-checks", type=int, default=DEFAULT_MAX_CHECKS, help="cap on live seat checks per run")
    parsed_arguments = argument_parser.parse_args(argv)
    if parsed_arguments.rebalance:
        return rebalance(parsed_arguments.dry_run, parsed_arguments.workers)
    return run(parsed_arguments.dry_run, parsed_arguments.workers, parsed_arguments.max_checks)


if __name__ == "__main__":
    sys.exit(main())
