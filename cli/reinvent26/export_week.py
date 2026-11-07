"""Export the live week as JSON for the bryanchasko.com/reinvent26 page.

`python3 -m reinvent26.export_week reinvent2026 --out <path>/week.json`

Reads the live schedule and the cached catalog (run `sessions` first),
computes held seats, favorites, and find-me windows, and attaches the
latest nightly watcher report. Read-only: never reserves or writes
personal time. The site template renders this file; regenerate it to
refresh the page.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

from reinvent26 import api, auth, cache, cli, findme, mapper

EVENT_ID = "reinvent2026"
CODE_RE = re.compile(r"\b([A-Z]{2,4}\d{3,4}(?:-R\d?|-S)?)\b")


def session_entry(catalog_session: dict) -> dict:
    """Catalog session narrowed to the fields the week page renders."""
    speakers = catalog_session.get("speakers") or []
    start = str(catalog_session.get("startTime") or "")
    return {
        "code": (catalog_session.get("abbreviation")
                 or catalog_session.get("code")
                 or catalog_session.get("sessionId")),
        "title": catalog_session.get("title") or "",
        "date": start[:10],
        "start": start[11:16],
        "end": str(catalog_session.get("endTime") or "")[11:16],
        "venue": catalog_session.get("venue") or "",
        "room": catalog_session.get("room") or "",
        "speakers": [speaker.get("name", "") for speaker in speakers
                     if isinstance(speaker, dict)],
        "level": catalog_session.get("level") or "",
        "format": (catalog_session.get("sessionType")
                   or catalog_session.get("type") or ""),
        "seat": (catalog_session.get("seatAvailability")
                 or catalog_session.get("seat_availability") or ""),
        "reservable": bool(catalog_session.get("isReservable")),
    }


def watcher_latest(watcher_dir: str) -> dict:
    """New-session codes from the latest nightly watcher report, if any."""
    try:
        names = sorted(report_file for report_file in os.listdir(watcher_dir)
                       if report_file.startswith("new-sessions-")
                       and report_file.endswith(".md"))
    except OSError:
        return {"report": None, "added": [], "opportunities": []}
    if not names:
        return {"report": None, "added": [], "opportunities": []}
    report = names[-1]
    text = open(os.path.join(watcher_dir, report), encoding="utf-8").read()
    added_section = re.split(r"## all added sessions",
                             text, maxsplit=1)
    added_text = added_section[1] if len(added_section) > 1 else ""
    opp_section = re.split(r"## opportunities.*?\n", text, maxsplit=1)
    opp_text = opp_section[1].split("##", 1)[0] if len(opp_section) > 1 else ""
    return {
        "report": report.replace("new-sessions-", "").replace(".md", ""),
        "added": sorted(set(CODE_RE.findall(added_text)) - {"none"}),
        "opportunities": sorted(set(CODE_RE.findall(opp_text)) - {"none"}),
    }


def _minus_minutes(clock: str, minutes: int) -> str:
    """Shift a HH:MM clock earlier; session times never cross midnight."""
    total = int(clock[:2]) * 60 + int(clock[3:5]) - minutes
    return f"{total // 60:02d}:{total % 60:02d}"


def _clock_to_minutes(clock: str) -> int:
    """HH:MM clock as minutes since midnight."""
    return int(clock[:2]) * 60 + int(clock[3:5])


def _gap_minutes(start: str, end: str) -> int:
    """Minutes between two HH:MM clocks on the same day."""
    return _clock_to_minutes(end) - _clock_to_minutes(start)


def _overlaps_lunch(start: str, end: str) -> bool:
    """True when a gap touches the 11:00-14:00 lunch window."""
    return start < "14:00" and end > "11:00"


def build_week(schedule: dict, catalog: list, watcher_dir: str,
               generated_at: str) -> dict:
    """Pure build: schedule plus catalog rows in, week dict out."""
    catalog_by_session_id = {
        catalog_row.get("sessionId"): catalog_row
        for catalog_row in catalog if isinstance(catalog_row, dict)
    }
    confirmed_items = cli._confirmed_items(schedule, catalog)
    for schedule_item in confirmed_items:
        catalog_details = catalog_by_session_id.get(
            schedule_item.get("sessionId"), {})
        for field_name, field_value in catalog_details.items():
            if field_name not in schedule_item or not schedule_item.get(field_name):
                schedule_item[field_name] = field_value
    schedule_node = (schedule.get("schedule", {})
                     if isinstance(schedule, dict) else {})
    reserved_ids = set(
        reservation if isinstance(reservation, str)
        else reservation.get("sessionId")
        for reservation in schedule_node.get("reserved", [])
    )
    held = [schedule_item for schedule_item in confirmed_items
            if schedule_item.get("sessionId") in reserved_ids
            or schedule_item.get("code") in reserved_ids]
    favorites = [schedule_item for schedule_item in confirmed_items
                 if schedule_item.get("sessionId") not in reserved_ids
                 and schedule_item.get("code") not in reserved_ids
                 and (schedule_item.get("startTime")
                      or schedule_item.get("sessionTime"))]
    windows = [
        {"date": str(gap_day), "start": gap_start.strftime("%H:%M"),
         "end": gap_end.strftime("%H:%M"),
         "minutes": gap_minutes, "part": gap_part}
        for gap_day, gap_start, gap_end, gap_minutes, gap_part
        in findme.day_gaps(held)
    ]
    held_entries = [session_entry(held_session) for held_session in held
                    if held_session.get("startTime")]
    favorites_entries = [session_entry(favorite_session)
                         for favorite_session in favorites
                         if favorite_session.get("startTime")]
    timeline = ([dict(held_entry, kind="held") for held_entry in held_entries]
                + [dict(open_window, kind="open")
                   for open_window in windows])
    timeline.sort(key=lambda timeline_entry: (timeline_entry.get("date", ""),
                                              timeline_entry.get("start", "")))
    venue_config = mapper._load_config()
    legs = []
    held_by_day: dict = {}
    for held_entry in held_entries:
        held_by_day.setdefault(held_entry["date"], []).append(held_entry)
    for day_date, day_held in held_by_day.items():
        ordered_held = sorted(day_held,
                              key=lambda held_entry: held_entry["start"])
        for first_session, second_session in zip(ordered_held,
                                                 ordered_held[1:]):
            transit_minutes = mapper._gap_needed(
                {"venue": first_session["venue"]},
                {"venue": second_session["venue"]}, venue_config)
            if first_session["venue"] == second_session["venue"]:
                transit_mode = "walk"
                transit_label = "in-venue walk, about 10 minutes"
            else:
                transit_mode = "shuttle"
                transit_label = (f"shuttle, about {transit_minutes} "
                                 "minutes (estimate)")
            legs.append({"kind": "leg", "date": day_date,
                         "start": first_session["end"],
                         "end": first_session["end"],
                         "ord": 1,
                         "from_venue": first_session["venue"],
                         "to_venue": second_session["venue"],
                         "from_room": first_session.get("room") or "",
                         "to_room": second_session.get("room") or "",
                         "mode": transit_mode, "label": transit_label})
    timeline = timeline + legs
    for day_date, day_held in held_by_day.items():
        ordered_held = sorted(day_held,
                              key=lambda held_entry: held_entry["start"])
        first_session_of_day = ordered_held[0]
        last_session_of_day = ordered_held[-1]
        timeline.append({
            "kind": "meal", "meal": "breakfast", "date": day_date,
            "start": "",
            "end": _minus_minutes(first_session_of_day["start"], 10),
            "when": f"morning, before {first_session_of_day['start']}",
            "ord": 1,
            "place": first_session_of_day["venue"], "state": "rule",
            "note": (f"breakfast near {first_session_of_day['venue']} — "
                     "grab-and-go or sit-down by the 20-minute gap; "
                     "room and serving hours posted on site")})
        for earlier_session, later_session in zip(ordered_held,
                                                  ordered_held[1:]):
            lunch_gap_minutes = _gap_minutes(earlier_session["end"],
                                              later_session["start"])
            if lunch_gap_minutes >= 20 and _overlaps_lunch(
                    earlier_session["end"], later_session["start"]):
                timeline.append({
                    "kind": "meal", "meal": "lunch", "date": day_date,
                    "start": earlier_session["end"],
                    "end": later_session["start"],
                    "when": (f"{earlier_session['end']}–"
                             f"{later_session['start']}"),
                    "ord": 1, "place": later_session["venue"],
                    "state": "rule",
                    "note": (f"{lunch_gap_minutes}-minute window near "
                             f"{later_session['venue']} — grab-and-go or "
                             "sit-down by the 20-minute rule")})
        closing_meal = "dinner"
        dinner_note = "dinner TBD — find me here after the last session"
        if last_session_of_day["end"] < "11:00":
            closing_meal = "brunch"
            dinner_note = ("back at the Venetian after the session: "
                           "last hallway window (wheels-up TBD)")
        if day_date == "2026-12-03":
            dinner_note = ("dinner TBD, then re:Play — "
                           "the one after-hours event")
        timeline.append({
            "kind": "meal", "meal": closing_meal, "date": day_date,
            "start": last_session_of_day["end"], "end": "",
            "when": f"after {last_session_of_day['end']}", "ord": 1,
            "place": "TBD", "state": "tbd", "note": dinner_note})
    for timeline_entry in timeline:
        timeline_entry.setdefault(
            "ord", 0 if timeline_entry["kind"] == "held" else 2)
    timeline.sort(key=lambda timeline_entry: (timeline_entry.get("date", ""),
                                              timeline_entry.get("start")
                                              or "00:00",
                                              timeline_entry.get("ord", 9)))
    return {
        "generated_at": generated_at,
        "event_id": EVENT_ID,
        "held": held_entries,
        "favorites": favorites_entries,
        "windows": windows,
        "timeline": timeline,
        "watcher": watcher_latest(watcher_dir),
    }


def run(event_id: str, out: str, watcher_dir: str) -> int:
    token = auth.stored_access_token()
    if not token:
        print("error: not signed in", file=sys.stderr)
        return 2
    catalog = cache.load_cached_sessions(event_id)
    if not catalog:
        print("error: no catalog cache", file=sys.stderr)
        return 2
    try:
        schedule = api.get_schedule(event_id, token)
    except api.EventsError as exc:
        print(f"error: schedule read failed: {exc}", file=sys.stderr)
        return 1
    week = build_week(schedule, catalog, watcher_dir,
                      _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d"))
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(week, handle, indent="\t")
        handle.write("\n")
    print(f"# wrote {out}: {len(week['held'])} held, "
          f"{len(week['favorites'])} favorites", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="reinvent26 export-week",
                                     description="export the live week as page JSON")
    parser.add_argument("event_id", nargs="?", default=EVENT_ID)
    parser.add_argument("--out", required=True, help="output JSON path")
    parser.add_argument("--watcher-dir", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "docs", "new-sessions"),
        help="nightly watcher report directory")
    args = parser.parse_args(argv)
    return run(args.event_id, args.out, args.watcher_dir)


if __name__ == "__main__":
    raise SystemExit(main())
