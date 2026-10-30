"""Event map and launch ledger generator.

Reads catalog JSON (default: .cache/reinvent2026/catalog.json or --catalog),
writes docs/event-map.md and docs/launch-ledger.md (or --out-dir).

Config-driven: topics, anchors, pins, gaps, and exclusions come from
data/reinvent2026/map-config.json, not code constants.

Inputs:
    catalog: list of session dicts from events API
    config: dict with topics, anchors, pins, gaps, exclusions

Outputs:
    docs/event-map.md: scheduled sessions, excluded sessions, TBD sessions
    docs/launch-ledger.md: sessions signaling new services/features

Side effects:
    Writes event-map.md and launch-ledger.md to output directory

Failure modes:
    FileNotFoundError: catalog or config not found
    json.JSONDecodeError: malformed JSON input
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta


# venue gap configuration (minutes)
SAME_VENUE_GAP = 0
NEAR_VENUE_GAP = 30
FAR_VENUE_GAP = 60


def _load_config() -> dict:
    """Load mapping config from data/reinvent2026/map-config.json."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    config_path = os.path.join(repo_root, "data", "reinvent2026", "map-config.json")
    with open(config_path, encoding="utf-8") as fh:
        return json.load(fh)


def _load_favorites(repo_root: str) -> set:
    """Load favorite session codes from data/reinvent2026/favorites.json."""
    fav_path = os.path.join(repo_root, "data", "reinvent2026", "favorites.json")
    try:
        with open(fav_path, encoding="utf-8") as fh:
            favorites_document = json.load(fh)
        items = favorites_document if isinstance(favorites_document, list) else favorites_document.get("sessions", [])
        return {favorite_entry.get("code") or favorite_entry.get("abbreviation") for favorite_entry in items if isinstance(favorite_entry, dict)}
    except (OSError, ValueError):
        return set()


def _load_catalog(path: str) -> list:
    """Load catalog from JSON file."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _parse(ts: str) -> datetime:
    """Parse ISO timestamp string to datetime."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))


def _text(session: dict) -> str:
    """Combine title and abstract for pattern matching."""
    return (session.get("title", "") + " " + (session.get("abstract") or "")).lower()


def _services(session: dict) -> str:
    """Join services list to lowercase string for pattern matching."""
    return " ".join(session.get("services") or []).lower()


def _when(session: dict) -> tuple | None:
    """Parse sessionTime to (start, end) datetime tuple or None."""
    st = session.get("sessionTime") or {}
    if not st.get("date") or not st.get("time"):
        return None
    try:
        start = datetime.fromisoformat(f"{st['date']}T{st['time']}")
        length = int(st.get("length") or 60)
        return start, start + timedelta(minutes=length)
    except (ValueError, TypeError):
        return None


def _base(code: str) -> str:
    """Strip -R or -R1 suffix from session code to get base code."""
    return re.sub(r"-R\d*$", "", code or "")


def _lvl(session: dict) -> str:
    """Extract level string (e.g. '300' from '300 - Intermediate')."""
    return str(session.get("level") or "").split(" ")[0]


def _tag(session: dict, topics: list) -> tuple:
    """Return (core, rel) topic matches based on title/abstract patterns.
    
    Core: title match only (for open-weight models to avoid abstract noise)
    Rel: abstract match only (for related topics)
    
    Args:
        session: session dict with title, abstract, services
        topics: list of topic configs with name, pattern, optional abstract_pattern
    
    Returns:
        (core, rel) tuple of matched topic names
    """
    core, rel = [], []
    title_lower = session.get("title", "").lower()
    abstract_lower = (session.get("abstract") or "").lower()
    for topic in topics:
        name = topic.get("name", "")
        pattern = topic.get("pattern", "")
        # open-weight: broad pattern on title, narrow model-name pattern on abstract
        if name == "open-weight models":
            if re.search(pattern, title_lower):
                core.append(name)
            elif topic.get("abstract_pattern") and re.search(topic["abstract_pattern"], abstract_lower):
                rel.append(name)
        else:
            if re.search(pattern, title_lower):
                core.append(name)
            elif re.search(pattern, abstract_lower):
                rel.append(name)
    return core, rel


def _is_anchor(session: dict, config: dict) -> bool:
    """Check if session is an anchor (topic match or pinned code).
    
    Anchor sessions get a weight boost of 1e6 and are scheduled first per day.
    
    Args:
        session: session dict with _core, _rel, abbreviation
        config: config dict with anchors list and pinned set
    
    Returns:
        True if session matches anchor criteria
    """
    anchors = config.get("anchors", [])
    pinned = set(config.get("pinned", []))
    core = session.get("_core", [])
    rel = session.get("_rel", [])
    code = session.get("abbreviation") or ""
    return bool(
        any(a in core or a in rel for a in anchors) or code in pinned
    )


def _is_bedrock_excluded(session: dict, config: dict) -> bool:
    """Check if session should be excluded due to bedrock keywords.
    
    Nova exception: sessions with 'nova' in text are never excluded.
    
    Args:
        session: session dict with title, abstract, services
        config: config dict with bedrock_excluded, bedrock_keywords, nova_exception
    
    Returns:
        True if session should be excluded
    """
    if not config.get("bedrock_excluded", True):
        return False
    keywords = config.get("bedrock_keywords", [])
    title = session.get("title", "").lower()
    text = _text(session)
    services_text = _services(session)
    # Nova exception: anything with nova is NOT excluded
    if config.get("nova_exception", True) and "nova" in text:
        return False
    return bool(re.search("|".join(keywords), title) or "bedrock" in services_text)


def _is_frontier_excluded(session: dict, config: dict) -> tuple:
    """Check if session should be excluded due to frontier/proprietary models.
    
    Returns (is_excluded, reason, abstract_flag).
    reason is 'bedrock' or 'frontier'.
    abstract_flag is True if only abstract matched frontier keywords (for human review).
    
    Args:
        session: session dict with title, abstract
        config: config dict with frontier_excluded, frontier_title_patterns, frontier_abstract_keywords
    
    Returns:
        (is_excluded, reason, abstract_flag) tuple
    """
    if not config.get("frontier_excluded", True):
        return (False, "", False)
    title = session.get("title", "").lower()
    abstract = (session.get("abstract") or "").lower()
    title_patterns = config.get("frontier_title_patterns", [])
    abstract_keywords = config.get("frontier_abstract_keywords", [])
    
    # Title matches - exclude immediately
    for pattern in title_patterns:
        if re.search(pattern, title):
            return (True, "frontier", False)
    
    # Abstract-only matches - keep but flag
    for kw in abstract_keywords:
        if kw in abstract and kw not in title:
            return (False, "mentions frontier models", True)
    
    return (False, "", False)


def _gap_needed(session_a: dict, session_b: dict, config: dict) -> int:
    """Return minimum gap in minutes between two sessions based on venue distance.
    
    Same venue: 0 min
    Near cluster (Venetian/Wynn/Caesars): 30 min
    Far (MGM Grand): 60 min
    
    Args:
        session_a: first session dict with venue
        session_b: second session dict with venue
        config: config dict with same_venue_gap, near_venue_gap, far_venue_gap, cluster_venues
    
    Returns:
        Minimum gap in minutes
    """
    same = config.get("same_venue_gap", SAME_VENUE_GAP)
    near = config.get("near_venue_gap", NEAR_VENUE_GAP)
    far = config.get("far_venue_gap", FAR_VENUE_GAP)
    cluster = set(config.get("cluster_venues", []))
    venue_a, venue_b = session_a.get("venue"), session_b.get("venue")
    if venue_a == venue_b:
        return same
    if venue_a in cluster and venue_b in cluster:
        return near
    return far


def _compatible(session_a: dict, session_b: dict, config: dict) -> bool:
    """Check if session_b can follow session_a respecting venue gap rules.
    
    Args:
        session_a: first session dict with _start, _end, venue
        session_b: second session dict with _start, _end, venue
        config: config dict with venue gap settings
    
    Returns:
        True if session_b starts after session_a plus required gap
    """
    gap = _gap_needed(session_a, session_b, config)
    return session_b.get("_start", datetime.max) >= session_a.get("_end", datetime.min) + timedelta(minutes=gap)


# scheduling weight constants (configurable)
ANCHOR_BONUS = 1e6
HELD_SEAT_BONUS_RESERVED_ONLY = 1e6
OPEN_SEAT_MULTIPLIER = 3.0
UNKNOWN_SEAT_MULTIPLIER = 2.0
FAVORITE_MULTIPLIER = 1.5
FAVORITE_MULTIPLIER_RESERVED_ONLY = 1.2
ADVANCED_LEVEL_MULTIPLIER = 1.1
DEFAULT_TOPIC_WEIGHT = 10.0
RELATED_ONLY_WEIGHT = 3.0
DEFAULT_FORMAT_WEIGHT = 5.0

# day name abbreviations (reused everywhere the dayname dict is repeated)
DAY_ABBREVIATIONS = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

# seat availability patterns
OPEN_SEATS = {"available", "limited", "veryLimited"}


def _weight(session: dict, config: dict) -> float:
    """Calculate session weight for scheduling in weighted interval scheduling.
    
    Weights encode scheduling priority:
    - reserved seats: +1e6 (fixed points, never churned)
    - reservable open: 3x base weight (scarcest resource)
    - reservable unknown: 2x base weight
    - favorite: 1.5x (1.2x when reserved_only mode)
    - level 300/400: 1.1x
    - anchor: +1e6 (scheduled first per day)
    
    Args:
        session: session dict with _start, _end, _core, _fav, isReservable, _seat, _reserved, type, level
        config: config dict with type_weight, topic_weight, reserved_only
    
    Returns:
        Weight value for scheduling priority
    """
    start = session.get("_start")
    end = session.get("_end")
    duration_minutes = (end - start).seconds / 60 if start and end else 60.0
    topic_weight = config.get("topic_weight", {})
    core = session.get("_core", [])
    is_favorite = session.get("_fav", False)
    reservable = session.get("isReservable", False)
    level = _lvl(session)
    format_weight_by_type = config.get("type_weight", {})

    weight = (max(topic_weight.get(t, DEFAULT_TOPIC_WEIGHT) for t in core) if core else RELATED_ONLY_WEIGHT) + duration_minutes / 60
    seat = session.get("_seat")
    if config.get("reserved_only"):
        # session format leads, topic fit breaks ties, already-held seats are fixed points
        weight = format_weight_by_type.get(session.get("type", ""), DEFAULT_FORMAT_WEIGHT)
        weight += (max(topic_weight.get(t, DEFAULT_TOPIC_WEIGHT) for t in core) * 0.5) if core else (2.0 if session.get("_rel") else 0.0)
        weight += duration_minutes / 120
        if is_favorite:
            weight *= FAVORITE_MULTIPLIER_RESERVED_ONLY
        if session.get("_reserved"):
            weight += HELD_SEAT_BONUS_RESERVED_ONLY
        return weight
    if reservable and seat in OPEN_SEATS:
        weight *= OPEN_SEAT_MULTIPLIER  # a reservable seat still open is the scarcest thing in the plan
    elif reservable and seat is None:
        weight *= UNKNOWN_SEAT_MULTIPLIER  # availability unknown: keep the old reservable preference
    # reservable but full: walk-up line only, same value as a walk-up session
    if is_favorite:
        weight *= FAVORITE_MULTIPLIER
    if level in ("300", "400"):
        weight *= ADVANCED_LEVEL_MULTIPLIER
    # Anchor boost so every compatible anchor lands first
    if _is_anchor(session, config):
        weight += ANCHOR_BONUS
    return weight


def _load_seats(repo_root: str) -> dict:
    """seatAvailability by code; prefers the full sweep, falls back to the topic-pool snapshot."""
    for name in ("seats-sweep.json", "seats.json"):
        path = os.path.join(repo_root, ".cache", "reinvent2026", name)
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh).get("seats", {})
        except (OSError, ValueError):
            continue
    return {}


def _load_reserved(repo_root: str) -> set:
    """sessionIds already reserved, from the .cache/reinvent2026/schedule.json snapshot of GET /schedule."""
    path = os.path.join(repo_root, ".cache", "reinvent2026", "schedule.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return set(json.load(fh).get("schedule", {}).get("reserved", []))
    except (OSError, ValueError):
        return set()


def _ledger_rows(ledger_sessions: list, signal: str) -> list:
    """Generate table rows for a ledger signal type."""
    rows = []
    for s in ledger_sessions:
        if s.get("_sig") != signal:
            continue
        st = s.get("_start")
        rows.append("| " + " | ".join([
            s.get("abbreviation", ""),
            f"{DAY_ABBREVIATIONS.get(st.weekday(), 'tbd')} {st:%m-%d}" if st else "tbd",
            f"{st:%H:%M}" if st else "tbd",
            s.get("venue") or "tbd",
            s.get("type", ""),
            signal,
            s.get("_kw", ""),
            ", ".join(s.get("services") or [])[:120].replace("|", "/"),
            (s.get("title") or "").replace("|", "/"),
            "",
        ]) + " |")
    return rows


def _build_map(catalog: list, config: dict, repo_root: str) -> tuple:
    """Build event map: chosen sessions, missed sessions, excluded, TBD."""
    favorites = _load_favorites(repo_root)
    seats = _load_seats(repo_root)
    reserved = _load_reserved(repo_root)
    reserved_only = bool(config.get("reserved_only"))
    topics = config.get("topics", [])
    pinned = set(config.get("pinned", []))

    pool, excluded, tbd = [], [], []
    for s in catalog:
        code = s.get("abbreviation") or ""
        core, rel = _tag(s, topics)
        fav = code in favorites
        s["_seat"] = seats.get(code)
        s["_core"] = core
        s["_rel"] = rel
        s["_fav"] = fav
        s["_reserved"] = s.get("sessionId") in reserved

        if reserved_only:
            # only seats we hold or can still book; any subject qualifies, topics only break ties
            if not (s["_reserved"] or (s.get("isReservable") and s["_seat"] in OPEN_SEATS)):
                continue
            if not s["_reserved"] and (_is_bedrock_excluded(s, config) or _is_frontier_excluded(s, config)[0]):
                continue
            w = _when(s)
            if w is None or s.get("isAllDaySession") or not s.get("venue"):
                continue
            s["_start"], s["_end"] = w
            pool.append(s)
            continue
        # off-topic sessions never enter any bucket (pool, watch list, or excluded)
        if not (core or rel or fav or code in pinned):
            continue

        # Pinned sessions bypass exclusions and always go to pool
        if code in pinned:
            w = _when(s)
            if w is None or s.get("isAllDaySession") or not s.get("venue"):
                tbd.append(s)
                continue
            s["_start"], s["_end"] = w
            pool.append(s)
            continue

        # Check bedrock exclusion
        if _is_bedrock_excluded(s, config):
            excluded.append(s)
            s["_exclude_reason"] = "bedrock"
            continue

        # Check frontier exclusion (title match)
        is_excluded, reason, abstract_flag = _is_frontier_excluded(s, config)
        if is_excluded:
            excluded.append(s)
            s["_exclude_reason"] = reason
            continue

        # Keep abstract-only frontier mentions but flag them
        if abstract_flag:
            s["_frontier_abstract"] = True

        w = _when(s)
        if w is None or s.get("isAllDaySession") or not s.get("venue"):
            tbd.append(s)
            continue

        s["_start"], s["_end"] = w
        if not (core or rel or fav):
            continue
        pool.append(s)

    # Weighted interval scheduling per day, repeat dedupe
    chosen, taken_bases = [], set()
    days = sorted({s.get("_start", datetime.max).date() for s in pool})
    dayname = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

    for day in days:
        cand = sorted(
            [s for s in pool if s.get("_start", datetime.max).date() == day and _base(s.get("abbreviation", "")) not in taken_bases],
            key=lambda x: x.get("_end", datetime.max),
        )
        if not cand:
            continue

        best = [0.0] * len(cand)
        prev = [-1] * len(cand)

        for i, s in enumerate(cand):
            ws = _weight(s, config)
            best[i] = ws
            prev[i] = -1
            for j in range(i):
                if _compatible(cand[j], s, config) and best[j] + ws > best[i]:
                    best[i] = best[j] + ws
                    prev[i] = j

        i = max(range(len(cand)), key=lambda k: best[k])
        picks = []
        while i != -1:
            picks.append(cand[i])
            i = prev[i]

        seen = set()
        for s in reversed(picks):
            b = _base(s.get("abbreviation", ""))
            if b in seen:
                continue
            seen.add(b)
            chosen.append(s)
        taken_bases |= seen

    chosen_codes = {s.get("abbreviation") for s in chosen}

    def _reason(s: dict) -> str:
        if _base(s.get("abbreviation", "")) in taken_bases:
            twin = next(c for c in chosen if _base(c.get("abbreviation", "")) == _base(s.get("abbreviation", "")))
            return f"repeat; scheduled as {twin.get('abbreviation')}"
        start_s = s.get("_start")
        end_s = s.get("_end")
        if start_s and end_s:
            clash = [c for c in chosen if c.get("_start") and c.get("_end") and c.get("_start") < end_s and start_s < c.get("_end")]
            if clash:
                return "time clash with " + ", ".join(c.get("abbreviation") for c in clash)
            near = [c for c in chosen if c.get("_start", datetime.max).date() == start_s.date()]
            venues = sorted({c.get("venue") for c in near if c.get("venue")})
            return "venue transition too tight (" + ", ".join(venues) + " that day)"
        return "no scheduled time"

    return chosen, excluded, tbd, chosen_codes, _reason, dayname


def _row(s: dict, config: dict, extra: str = "", dayname: dict | None = None, show_real_time: bool = False) -> str:
    """Format a session row for markdown table."""
    session_start = s.get("_start")
    end = s.get("_end")
    
    # Use catalog times for excluded/tbd sessions (show_real_time=True)
    if show_real_time:
        stime = s.get("sessionTime") or {}
        st_real = stime.get("date") and stime.get("time")
        if st_real:
            st_parsed = datetime.fromisoformat(f"{stime['date']}T{stime['time']}")
            d = f"{dayname.get(st_parsed.weekday(), 'tbd')} {st_parsed:%m-%d}"
            t = f"{st_parsed:%H:%M}-{(st_parsed + timedelta(minutes=int(stime.get('length') or 60))):%H:%M}"
        else:
            d = "tbd"
            t = "tbd"
    elif session_start:
        d = f"{dayname.get(session_start.weekday(), 'tbd')} {session_start:%m-%d}" if session_start else "tbd"
        t = f"{session_start:%H:%M}-{end:%H:%M}" if session_start and end else "tbd"
    else:
        d = "tbd"
        t = "tbd"
    
    core = s.get("_core", [])
    rel = s.get("_rel", [])
    # Only show "favorite" if it's actually a favorite AND has no core/rel
    # Sessions without ANY match should show empty topics (they were excluded from pool)
    if core or rel:
        topics = ", ".join(core + [f"({r})" for r in rel])
    elif s.get("_fav"):
        topics = "favorite"
    else:
        topics = ""
    seat = "reserve" if s.get("isReservable") else "walk-up"
    if s.get("_reserved"):
        seat = "RESERVED"
    elif s.get("isReservable") and s.get("_seat"):
        seat = {"available": "reserve (open)", "limited": "reserve (limited)", "veryLimited": "reserve (very limited)",
                "unavailable": "full, walk-up line", "walkUp": "walk-up"}.get(s["_seat"], seat)
    if session_start and _is_anchor(s, config):
        seat = "ANCHOR, " + seat
    table_columns = [
        s.get("abbreviation", ""),
        d,
        t,
        s.get("venue") or "tbd",
        s.get("type", ""),
        _lvl(s),
        seat,
        topics,
        (s.get("title") or "").replace("|", "/"),
    ]
    # Add frontier abstract flag column if present
    if s.get("_frontier_abstract"):
        table_columns.append("frontier abstract")
    if extra:
        table_columns.append(extra)
    return "| " + " | ".join(table_columns) + " |"


def _write_event_map(chosen: list, excluded: list, tbd: list, pool: list,
                     chosen_codes: set, config: dict, out_dir: str,
                     dayname: dict, reason_func=None) -> None:
    """Write docs/event-map.md."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_path = os.path.join(out_dir, "event-map.md")
    os.makedirs(out_dir, exist_ok=True)

    lines = []
    lines += ["# re:invent 2026 event map", "",
              "coordination page for the hackathon team. built from the live events api catalog, pulled at build time. regenerate by re-pulling the catalog; session times and rooms move until the event",
              "", "## ground rules", "",
              "- home base: venetian",
              "- strip cluster: venetian, wynn/encore, caesars palace, caesars forum. 30 minutes between venues inside the cluster",
              "- assumption: caesars forum treated as part of the cluster (behind the linq, walkable from caesars palace). flag if that is wrong",
              "- mgm grand sits at the south end of the strip. planner wants 60+ minutes to cross between mgm and the cluster, so mgm sessions group into mgm blocks",
              "- priority: reserved seats wall to wall. reservable sessions weigh 2x walk-ups, title matches weigh 1.4x abstract-only matches, favorites 1.5x, 300/400 level 1.1x",
              "- amazon bedrock out except nova; frontier and proprietary third-party model sessions out; open weight and open source models preferred and tracked as the topic \"open-weight models\"",
              "- repeats (-R, -R1) scheduled once, on whichever day fits the plan best",
              "- reservations: seating opened 6 oct and full reserve/cancel write access 8 oct per the hackathon page. verify with a live reserve call before relying on it",
              "- times as listed in the catalog (las vegas local)", "",
              "## venue map", "", "```",
              "north",
              "  wynn / encore",
              "      |   ~10-15 min walk",
              "  venetian / palazzo  (home base)",
              "      |   ~10-15 min walk",
              "  caesars forum (behind the linq)",
              "      |   ~10 min walk",
              "  caesars palace",
              "      |",
              "      |   ~2 miles, monorail / shuttle / rideshare: 30-45 min door to door",
              "      |",
              "  mgm grand",
              "south", "```", "",
              "walk times are rough planning numbers, not measured. the official re:invent shuttle map will be authoritative once published",
              "", "## topics tracked", "",
              ", ".join(t.get("name", "") for t in config.get("topics", [])),
              "", "## build order", "",
              "- step 1: pin every amazon leo session as an anchor (marked ANCHOR in the seat column), plus bryan-approved pins",
              "- step 2: fill open time around the anchors, ranked by topic weight",
              "", "## anchors", "", "| code | day | time | venue | type | level | seat | topics | title |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]

    anchors = sorted([s for s in pool if _is_anchor(s, config)], key=lambda x: x.get("_start", datetime.max))
    for s in anchors:
        lines.append(_row(s, config, dayname=dayname))

    lines += ["", "", "## schedule", ""]

    reserved_min = walk_min = 0
    days = sorted({s.get("_start", datetime.max).date() for s in chosen})
    for day in days:
        ds = sorted([s for s in chosen if s.get("_start", datetime.max).date() == day], key=lambda x: x.get("_start", datetime.min))
        if not ds:
            continue
        lines += [f"### {dayname.get(day.weekday(), 'day')} {day:%m-%d}", "", "| code | day | time | venue | type | level | seat | topics | title |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for s in ds:
            lines.append(_row(s, config, dayname=dayname))
            m = (s.get("_end", datetime.min) - s.get("_start", datetime.max)).seconds // 60
            if s.get("isReservable"):
                reserved_min += m
            else:
                walk_min += m
        lines.append("")

    lines += [f"totals: {len(chosen)} sessions, {reserved_min//60}h{reserved_min%60:02d} reserved-seat time, {walk_min//60}h{walk_min%60:02d} walk-up time", ""]

    lines += ["## would love to attend but not conducive to logistics", "",
              "every topic session that did not fit, so teammates can see the interest and cover it or flag a swap", ""]

    missed = [s for s in pool if s.get("abbreviation") not in chosen_codes]
    by_topic = defaultdict(list)
    for s in missed:
        # Use first topic match, or empty if none (shouldn't happen for pool members)
        key = (s.get("_core") or s.get("_rel"))[0] if (s.get("_core") or s.get("_rel")) else ""
        if not key:
            key = "favorite" if s.get("_fav") else "untagged"
        by_topic[key].append(s)

    topics_order = [t.get("name", "") for t in config.get("topics", [])] + ["favorite"]
    for name in topics_order:
        grp = sorted(by_topic.get(name, []), key=lambda x: x.get("_start", datetime.max))
        if not grp:
            continue
        lines += [f"### {name}", "", "| code | day | time | venue | type | level | seat | topics | title |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for s in grp:
            lines.append(_row(s, config, dayname=dayname))
        lines.append("")

    if tbd:
        lines += ["## not yet timed (watch list)", "", "| code | day | time | venue | type | level | seat | topics | title |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for s in tbd:
            lines.append(_row(s, config, dayname=dayname, show_real_time=True))
        lines.append("")

    lines += ["## excluded: bedrock and frontier models", "", "kept for the record so nothing gets lost. not planned", "", "| code | day | time | venue | type | level | seat | topics | title | reason |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in sorted(excluded, key=lambda x: x.get("_start", datetime.max) or datetime.max):
        reason = s.get("_exclude_reason", "")
        lines.append(_row(s, config, extra=reason, dayname=dayname, show_real_time=True))
    lines.append("")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _write_launch_ledger(catalog: list, out_dir: str) -> None:
    """Write docs/launch-ledger.md."""
    NEW = r"\bnew\b|newly|launch|introduc|announc|what's new|preview|now available|just released|first look|latest|next-generation|next generation"
    NEW_A = r"newly launched|recently launched|just launched|new capabilit\w*|new features?|new services?|announc\w*|introduc\w*|preview|now available|what's new|generally available"

    led = []
    for s in catalog:
        title = s.get("title", "")
        abstract = s.get("abstract") or ""
        m_t = re.findall(NEW, title.lower().replace("launchdarkly", ""))
        m_a = re.findall(NEW_A, abstract.lower())
        if not (m_t or m_a):
            continue

        st = s.get("sessionTime") or {}
        if st.get("date") and st.get("time"):
            start = datetime.fromisoformat(f"{st['date']}T{st['time']}")
            length = int(st.get("length", 60))
            end = start + timedelta(minutes=length)
        else:
            start = end = None

        s2 = dict(s)
        s2["_start"] = start
        s2["_end"] = end
        s2["_sig"] = "title" if m_t else "abstract"
        s2["_kw"] = ", ".join(sorted(set(m_t + m_a)))
        led.append(s2)

    led.sort(key=lambda x: (x.get("_sig") != "title", x.get("_start") or datetime.max))

    dayname = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

    lines = ["# re:invent 2026 launch ledger", "",
             "running record of sessions that signal new services, features, or launches. source: live events api catalog. keyword signal on title (strong) or abstract (weak); confirm against the aws news blog and keynote announcements as they land",
             "", "## how to use", "",
             "- title-signal rows are the likeliest launch sessions",
             "- add a `confirmed launch` note with a source url when an announcement lands",
             "- services column helps map sessions to product areas",
             "", f"title signals: {sum(1 for s in led if s.get('_sig') == 'title')}, abstract signals: {sum(1 for s in led if s.get('_sig') == 'abstract')}", ""]

    lines += ["## title signal", "",
              "| code | day | time | venue | type | signal | keywords | services | title | confirmed launch |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in led:
        if s.get("_sig") != "title":
            continue
        st = s.get("_start")
        lines.append("| " + " | ".join([
            s.get("abbreviation", ""),
            f"{dayname.get(st.weekday(), 'tbd')} {st:%m-%d}" if st else "tbd",
            f"{st:%H:%M}" if st else "tbd",
            s.get("venue") or "tbd",
            s.get("type", ""),
            "title",
            s.get("_kw", ""),
            ", ".join(s.get("services") or [])[:120].replace("|", "/"),
            (s.get("title") or "").replace("|", "/"),
            "",
        ]) + " |")
    lines.append("")

    lines += ["## abstract signal", "",
              "| code | day | time | venue | type | signal | keywords | services | title | confirmed launch |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in led:
        if s.get("_sig") != "abstract":
            continue
        st = s.get("_start")
        lines.append("| " + " | ".join([
            s.get("abbreviation", ""),
            f"{dayname.get(st.weekday(), 'tbd')} {st:%m-%d}" if st else "tbd",
            f"{st:%H:%M}" if st else "tbd",
            s.get("venue") or "tbd",
            s.get("type", ""),
            "abstract",
            s.get("_kw", ""),
            ", ".join(s.get("services") or [])[:120].replace("|", "/"),
            (s.get("title") or "").replace("|", "/"),
            "",
        ]) + " |")
    lines.append("")

    out_path = os.path.join(out_dir, "launch-ledger.md")
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="reinvent26 map", description="build event map and launch ledger")
    parser.add_argument("--catalog", default=None, help="catalog JSON path (default: .cache/reinvent2026/sessions.json - never write catalog from tests)")
    parser.add_argument("--out-dir", default=None, help="output directory (default: docs)")
    args = parser.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    config = _load_config()

    # Test guard: require explicit --out-dir under pytest to prevent writes to repo
    if os.environ.get("PYTEST_CURRENT_TEST") and args.out_dir is None:
        print("error: --out-dir is required when running under pytest", file=sys.stderr)
        raise SystemExit(2)

    # Default catalog path
    if args.catalog is None:
        # Try both catalog.json and sessions.json for compatibility
        cat_path = os.path.join(repo_root, ".cache", "reinvent2026", "catalog.json")
        sess_path = os.path.join(repo_root, ".cache", "reinvent2026", "sessions.json")
        if os.path.exists(cat_path):
            args.catalog = cat_path
        elif os.path.exists(sess_path):
            args.catalog = sess_path
        else:
            print(f"error: catalog not found at {cat_path} or {sess_path}; run 'python -m reinvent26 sessions reinvent2026' first", file=sys.stderr)
            print(f"note: catalog persists in project at .cache/reinvent2026/catalog.json; tests never write catalog", file=sys.stderr)
            raise SystemExit(2)

    catalog = _load_catalog(args.catalog)
    out_dir = args.out_dir or os.path.join(repo_root, "docs")

    chosen, excluded, tbd, chosen_codes, reason_func, dayname = _build_map(catalog, config, repo_root)
    pool = [s for s in catalog if s.get("_start")]

    _write_event_map(chosen, excluded, tbd, pool, chosen_codes, config, out_dir, dayname)
    _write_launch_ledger(catalog, out_dir)

    print(f"event map written to {out_dir}/event-map.md")
    print(f"launch ledger written to {out_dir}/launch-ledger.md")


if __name__ == "__main__":
    main()