"""Sync week.json meals, open windows and travel legs to personal time.

Input: the bryan-chasko-com week.json timeline. Sessions (kind "held")
are skipped; everything else becomes one personal-time entry with
event-local wall-clock times rounded to 5 minutes (start floors, end
ceils, so the block covers the original span).

Idempotence: a local state file maps our stable entry key to the api
personalTimeId. Unknown ids fall back to matching live schedule entries
by title + start, so a lost state file updates instead of duplicating.
Only entries recorded in state (or matched to a desired entry) are ever
updated or deleted; hand-made personal time is left alone.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date as date_cls

from reinvent26 import api
from reinvent26.schedule import validate_personal_time

STEP = 5
DEFAULT_MINUTES = {"breakfast": 30, "lunch": 45, "brunch": 60, "dinner": 90}
DEFAULT_LEG_MINUTES = 15
DEFAULT_LIVE_LOCATION = "Personal"


def state_file(event_id: str) -> str:
    override = os.environ.get("REINVENT26_PERSONAL_TIME_STATE")
    if override:
        return override
    return os.path.join(os.path.expanduser("~"), ".config", "reinvent26",
                        f"personal-time-{event_id}.json")


def load_state(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


def to_minutes(hhmm: str) -> int | None:
    if not hhmm:
        return None
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def floor5(minutes: int) -> int:
    return minutes - minutes % STEP


def ceil5(minutes: int) -> int:
    return -(-minutes // STEP) * STEP


def stamp(day: str, minutes: int) -> str:
    return f"{day}T{minutes // 60:02d}:{minutes % 60:02d}:00"


def _trim(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _room_short(room: str) -> str:
    return (room or "").split("|")[-1].strip()


def _clean(text: str) -> str:
    # live api returns 400 "could not be applied" for "|" (probed 2026 Events API)
    return (text or "").replace(" | ", ", ").replace("|", ",")


def _place(venue: str, room: str) -> str:
    venue = _clean(venue).strip()
    room = _clean(room).strip()
    if venue and room:
        return f"{venue}, {room}"
    return venue or room


def _leg_minutes(label: str) -> int:
    m = re.search(r"about (\d+) minutes", label or "")
    return int(m.group(1)) if m else DEFAULT_LEG_MINUTES


def _span(entry: dict) -> tuple:
    """(start_min, end_min) before rounding; either may be derived."""
    kind = entry.get("kind")
    start = to_minutes(entry.get("start", ""))
    end = to_minutes(entry.get("end", ""))
    if kind == "leg":
        end = start + _leg_minutes(entry.get("label", "")) if start is not None else None
    elif kind == "meal":
        dur = DEFAULT_MINUTES.get(entry.get("meal", ""), 45)
        if start is None and end is not None:
            start = end - dur
        elif end is None and start is not None:
            end = start + dur
    return start, end


def _title(entry: dict) -> str:
    kind = entry.get("kind")
    if kind == "meal":
        meal = (entry.get("meal") or "meal").capitalize()
        place = entry.get("place") or ""
        if not place or place.upper() == "TBD":
            return f"{meal} (place TBD)"
        return f"{meal} near {place}"
    if kind == "open":
        return "Open window: find Bryan"
    if kind == "leg":
        mode = (entry.get("mode") or "travel").capitalize()
        if entry.get("from_venue") != entry.get("to_venue"):
            return f"{mode} to {entry.get('to_venue')}"
        return f"{mode} to {_room_short(entry.get('to_room', ''))}"
    return (entry.get("title") or kind or "Personal time")[:128]


def _description(entry: dict, location: str) -> str:
    note = entry.get("note")
    if not note and entry.get("kind") == "leg":
        note = (f"{entry.get('label', 'travel')}: "
                f"{_place(entry.get('from_venue'), entry.get('from_room'))} "
                f"to {_place(entry.get('to_venue'), entry.get('to_room'))}")
    if not note and entry.get("kind") == "open":
        where = f" near {location}" if location else ""
        note = (f"{entry.get('minutes', '')}-minute {entry.get('part', '')} "
                f"open window{where}; find Bryan here")
    return _trim(note or _title(entry), 250)


def _location(entry: dict, here: str) -> str:
    kind = entry.get("kind")
    if kind == "meal":
        place = entry.get("place") or ""
        return "" if place.upper() == "TBD" else place
    if kind == "leg":
        return _place(entry.get("to_venue"), entry.get("to_room"))
    return here


def build_entries(week: dict) -> tuple:
    """Return (entries, skipped) from a week.json dict.

    entries: dicts with key/title/description/location/start/end.
    skipped: dicts with key/title/reason.
    """
    entries, skipped = [], []
    seq: dict = {}
    here_by_day: dict = {}
    for raw in week.get("timeline") or []:
        kind = raw.get("kind")
        day = raw.get("date", "")
        if kind == "held":
            here_by_day[day] = _place(raw.get("venue"), raw.get("room"))
            continue
        sub = raw.get("meal") or raw.get("mode") or raw.get("part") or ""
        group = (day, kind, sub)
        seq[group] = seq.get(group, 0) + 1
        key = f"{day}:{kind}:{sub}:{seq[group]}"
        title = _title(raw)
        location = _location(raw, here_by_day.get(day, ""))
        if kind == "leg":
            here_by_day[day] = location
        start, end = _span(raw)
        if start is None or end is None:
            skipped.append({"key": key, "title": title, "reason": "no time"})
            continue
        start, end = floor5(start), ceil5(end)
        if start < 0 or end >= 24 * 60 or end <= start:
            reason = ("crosses midnight" if start < 0 or end >= 24 * 60
                      else "zero length")
            skipped.append({"key": key, "title": title, "reason": reason,
                            "date": day})
            continue
        try:
            date_cls.fromisoformat(day)
        except ValueError:
            skipped.append({"key": key, "title": title, "reason": "bad date"})
            continue
        item = {
            "key": key,
            "title": _clean(title)[:128],
            "description": _clean(_description(raw, location)),
            "location": _clean(location)[:255] or None,
            "start": stamp(day, start),
            "end": stamp(day, end),
        }
        try:
            validate_personal_time(item["title"], item["start"], item["end"],
                                   description=item["description"],
                                   location=item["location"])
        except ValueError as e:
            skipped.append({"key": key, "title": title, "reason": str(e)})
            continue
        entries.append(item)
    return entries, skipped


def schedule_personal_time(sched) -> list:
    """personalTime list from a GetSchedule payload (wrapped or bare)."""
    if not isinstance(sched, dict):
        return []
    node = sched.get("schedule") if isinstance(sched.get("schedule"), dict) else sched
    out = node.get("personalTime") or []
    return [p for p in out if isinstance(p, dict)]


def _live_location(live: dict):
    # the api stores an omitted location as "Personal"
    loc = live.get("location") or None
    return None if loc == DEFAULT_LIVE_LOCATION else loc


def _same(entry: dict, live: dict) -> bool:
    return (live.get("title") == entry["title"]
            and live.get("description") == entry["description"]
            and _live_location(live) == entry["location"]
            and live.get("startDateTime") == entry["start"]
            and live.get("endDateTime") == entry["end"])


def plan(entries: list, live: list, state: dict) -> list:
    """Actions: dicts with op in create/update/noop/delete.

    Resolution order per entry: state id still live, then an unclaimed
    live block with the same title + start, then create. Extra live
    blocks matching a desired title + start are duplicates and deleted.
    State ids whose key is no longer desired are deleted.
    """
    by_id = {p.get("personalTimeId"): p for p in live if p.get("personalTimeId")}
    claimed: set = set()
    actions = []
    for e in entries:
        pid = state.get(e["key"])
        hit = by_id.get(pid) if pid in by_id and pid not in claimed else None
        if hit is None:
            for p in live:
                cand = p.get("personalTimeId")
                if (cand not in claimed and p.get("title") == e["title"]
                        and p.get("startDateTime") == e["start"]):
                    hit = p
                    break
        if hit is None:
            actions.append({"op": "create", "entry": e, "id": None})
            continue
        claimed.add(hit["personalTimeId"])
        op = "noop" if _same(e, hit) else "update"
        actions.append({"op": op, "entry": e, "id": hit["personalTimeId"]})
    wanted = {(e["title"], e["start"]) for e in entries}
    owned = set(state.values())
    for p in live:
        pid = p.get("personalTimeId")
        if pid in claimed:
            continue
        ours = pid in owned
        dup = (p.get("title"), p.get("startDateTime")) in wanted
        if ours or dup:
            claimed.add(pid)
            actions.append({"op": "delete", "id": pid,
                            "entry": {"key": "", "title": p.get("title", ""),
                                      "start": p.get("startDateTime", ""),
                                      "end": p.get("endDateTime", "")}})
    return actions


def format_table(actions: list, skipped: list) -> str:
    lines = [f"{'op':<7} {'start':<19} {'end':<5}  {'title':<36} location"]
    for a in actions:
        e = a["entry"]
        lines.append(f"{a['op']:<7} {e.get('start', ''):<19} "
                     f"{e.get('end', '')[11:16]:<5}  {e.get('title', '')[:36]:<36} "
                     f"{(e.get('location') or '')[:48]}")
    for s in skipped:
        lines.append(f"{'skip':<7} {s.get('key', ''):<25} {s.get('title', '')[:36]:<36} "
                     f"({s['reason']})")
    return "\n".join(lines)


def counts(actions: list, skipped: list) -> dict:
    out = {"planned": len(actions), "create": 0, "update": 0, "noop": 0,
           "delete": 0, "skipped": len(skipped)}
    for a in actions:
        out[a["op"]] += 1
    return out


def apply(event_id: str, token: str, actions: list, state: dict) -> tuple:
    """Execute the plan, resolve new ids from one GetSchedule.

    Returns (new_state, failures). A 400 on one entry is recorded and the
    run continues; any other write error stops further writes (never a
    blind retry) and the state is still resolved from GetSchedule so the
    next run reconciles instead of duplicating.
    """
    new_state = {}
    failures = []
    for a in actions:
        e = a["entry"]
        try:
            if a["op"] == "delete":
                api.delete_personal_time(event_id, token, a["id"])
            elif a["op"] == "update":
                api.update_personal_time(event_id, token, a["id"], e["title"],
                                         e["start"], e["end"],
                                         description=e["description"],
                                         location=e["location"])
                new_state[e["key"]] = a["id"]
            elif a["op"] == "noop":
                new_state[e["key"]] = a["id"]
            elif a["op"] == "create":
                api.create_personal_time(event_id, token, e["title"],
                                         e["start"], e["end"],
                                         description=e["description"],
                                         location=e["location"])
        except api.EventsError as err:
            failures.append({"op": a["op"], "entry": e, "error": str(err)})
            if a["op"] in ("update", "noop"):
                new_state[e["key"]] = a["id"]
            if err.status != 400:
                break
    live = schedule_personal_time(api.get_schedule(event_id, token))
    live_ids = {p.get("personalTimeId") for p in live}
    new_state = {k: v for k, v in new_state.items() if v in live_ids}
    taken = set(new_state.values())
    for a in actions:
        e = a["entry"]
        if a["op"] != "create" or e["key"] in new_state:
            continue
        for p in live:
            pid = p.get("personalTimeId")
            if (pid not in taken and p.get("title") == e["title"]
                    and p.get("startDateTime") == e["start"]):
                new_state[e["key"]] = pid
                taken.add(pid)
                break
    return new_state, failures


def verify(entries: list, live: list) -> list:
    """Problems list: each desired title + start must appear exactly once."""
    problems = []
    for e in entries:
        n = sum(1 for p in live if p.get("title") == e["title"]
                and p.get("startDateTime") == e["start"])
        if n != 1:
            problems.append(f"{e['start']} {e['title']}: found {n}")
    return problems
