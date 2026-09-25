"""Pure schedule logic: clash detection, free-slot search, topic matching.

All functions are pure (no network) so they stay unit-testable.
Session dicts follow the Events API shape: sessionId/code, title, level,
tracks, topics, services, startTime/endTime (ISO strings).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))


def find_clashes(items: list) -> list:
    """Return pairs of items whose time ranges overlap.

    Each item needs startTime/endTime plus sessionId or title for reporting.
    """
    timed = [i for i in items if i.get("startTime") and i.get("endTime")]
    timed.sort(key=lambda i: i["startTime"])
    clashes = []
    for a, b in zip(timed, timed[1:]):
        if _parse(b["startTime"]) < _parse(a["endTime"]):
            clashes.append((a, b))
    return clashes


def fits_in(start: str, end: str, window_start: str, window_end: str) -> bool:
    return _parse(window_start) <= _parse(start) and _parse(end) <= _parse(
        window_end
    )


def find_open_slots(
    sessions: list, windows: list, scheduled: list | None = None
) -> list:
    """Return sessions that fit fully inside any free window and do not clash
    with already scheduled items."""
    scheduled = scheduled or []
    out = []
    for s in sessions:
        if not (s.get("startTime") and s.get("endTime")):
            continue
        if not any(
            fits_in(s["startTime"], s["endTime"], w["start"], w["end"])
            for w in windows
        ):
            continue
        if find_clashes(scheduled + [s]):
            continue
        out.append(s)
    return out


def normalize_session(s: dict) -> dict:
    """Map a live catalog item onto canonical schedule fields.

    The live API carries the session code in `abbreviation` (not `code`)
    and the time in `sessionTime: {date, time, length}` (24h, minutes)
    instead of ISO startTime/endTime. This fills in the canonical fields
    and leaves everything else untouched; items without usable times
    stay timeless (kept by filters, skipped by clash/slot logic).
    Idempotent: already-canonical items pass through unchanged.
    """
    s = dict(s)
    if not s.get("code") and s.get("abbreviation"):
        s["code"] = s["abbreviation"]
    if not s.get("id") and s.get("personalTimeId"):
        s["id"] = s["personalTimeId"]
    for iso_key, alt_key in (("startTime", "startDateTime"),
                             ("endTime", "endDateTime")):
        if not s.get(iso_key) and s.get(alt_key):
            try:
                _parse(str(s[alt_key]))
                s[iso_key] = s[alt_key]
            except ValueError:
                pass
    st = s.get("sessionTime") or {}
    if not s.get("startTime") and st.get("date") and st.get("time"):
        try:
            hh, mm = str(st["time"]).split(":")
            start = datetime.strptime(
                f"{st['date']}T{int(hh):02d}:{int(mm):02d}:00",
                "%Y-%m-%dT%H:%M:%S",
            )
            minutes = int(str(st.get("length") or 0))
            end = start + timedelta(minutes=max(minutes, 0))
            s["startTime"] = start.strftime("%Y-%m-%dT%H:%M:%S")
            s["endTime"] = end.strftime("%Y-%m-%dT%H:%M:%S")
        except (ValueError, TypeError):
            pass
    return s


def normalize_sessions(sessions: list) -> list:
    return [normalize_session(s) if isinstance(s, dict) else s
            for s in sessions]


def _text_fields(s: dict) -> str:
    parts = [s.get("title", ""), s.get("code", ""), s.get("abbreviation", "")]
    for key in ("tracks", "topics", "services", "level", "sessionType"):
        v = s.get(key)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
        elif v:
            parts.append(str(v))
    return " ".join(parts).lower()


def match_topics(sessions: list, keywords: list, exclude=None) -> list:
    """Rank sessions by keyword hits across title/tracks/topics/services."""
    exclude = {e.lower() for e in (exclude or [])}
    keys = [k.lower() for k in keywords]
    ranked = []
    for s in sessions:
        text = _text_fields(s)
        if any(e in text for e in exclude):
            continue
        hits = sum(1 for k in keys if k in text)
        if hits:
            ranked.append((hits, s))
    ranked.sort(key=lambda t: -t[0])
    return [s for _, s in ranked]


def _hhmm(value: str) -> time:
    """Parse HH:MM (24h). Raises ValueError on bad input."""
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"expected HH:MM, got {value!r}")
    hour, minute = int(parts[0]), int(parts[1])
    return time(hour, minute)


def _overlaps(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def filter_by_time(
    sessions: list,
    not_before: str | None = None,
    not_after: str | None = None,
    lunch: str | None = None,
) -> list:
    """Drop sessions outside a daily time-of-day window.

    not_before/not_after are HH:MM bounds applied to the session start.
    lunch is HH:MM-HH:MM; sessions overlapping it are blocked out.
    Sessions without timestamps are kept (they cannot be judged).
    """
    lo = _hhmm(not_before) if not_before else None
    hi = _hhmm(not_after) if not_after else None
    lunch_range = None
    if lunch:
        bounds = lunch.split("-")
        if len(bounds) != 2:
            raise ValueError(f"expected HH:MM-HH:MM, got {lunch!r}")
        lunch_range = (_hhmm(bounds[0]), _hhmm(bounds[1]))
    out = []
    for s in sessions:
        if not s.get("startTime"):
            out.append(s)
            continue
        try:
            start = _parse(s["startTime"]).time()
            end = _parse(s["endTime"]).time() if s.get("endTime") else start
        except ValueError:
            out.append(s)
            continue
        if lo is not None and start < lo:
            continue
        if hi is not None and start > hi:
            continue
        if lunch_range is not None and _overlaps(start, end, *lunch_range):
            continue
        out.append(s)
    return out


def filter_by_day(sessions: list, day: str | None) -> list:
    """Keep sessions starting on day (YYYY-MM-DD). None/empty day is a no-op."""
    if not day:
        return sessions
    return [s for s in sessions if (s.get("startTime") or "").startswith(day)]


def find_offbeat(sessions: list, keywords: list, exclude=None) -> dict | None:
    """Pick one session with nothing to do with the given keywords.

    Returns the earliest-starting zero-hit session, or None when every
    session matches. Deterministic for stable shortlists.
    """
    exclude = {e.lower() for e in (exclude or [])}
    keys = [k.lower() for k in keywords]
    outsiders = []
    for s in sessions:
        text = _text_fields(s)
        if any(e in text for e in exclude):
            continue
        if not any(k in text for k in keys):
            outsiders.append(s)
    outsiders.sort(key=lambda s: (s.get("startTime") or "", s.get("sessionId") or ""))
    return outsiders[0] if outsiders else None


def stack_keywords(resources: list) -> list:
    """Map live Amazon Web Services resource types to catalog keywords.

    Input: list of dicts with at least a service/type key, e.g.
    {"service": "Amazon Web Services Lambda"}. Output: sorted keyword list.
    """
    mapping = {
        "lambda": ["serverless", "lambda", "event-driven"],
        "dynamodb": ["dynamodb", "nosql", "data modeling"],
        "apigateway": ["api gateway", "rest", "http api"],
        "bedrock": ["bedrock", "generative ai", "agents"],
        "sagemaker": ["sagemaker", "machine learning"],
        "ecs": ["containers", "ecs", "fargate"],
        "eks": ["kubernetes", "eks", "containers"],
        "rds": ["rds", "relational", "aurora"],
        "s3": ["s3", "storage", "vectors"],
        "cloudwatch": ["observability", "cloudwatch", "alarms"],
        "eventbridge": ["eventbridge", "event-driven"],
        "stepfunctions": ["step functions", "orchestration"],
    }
    out: set = set()
    for r in resources:
        blob = " ".join(str(v) for v in r.values()).lower().replace(" ", "")
        for key, words in mapping.items():
            if key in blob:
                out.update(words)
    return sorted(out)


def summarize(s: dict) -> str:
    code = (s.get("code") or s.get("sessionId") or s.get("id")
            or s.get("blockId", "?"))
    start = s.get("startTime") or s.get("start", "?")
    end = s.get("endTime") or s.get("end", "?")
    return (
        f"{code} | {s.get('title', '?')} | {s.get('level', '?')} | "
        f"{start}->{end} | "
        f"{s.get('room', '?')}"
    )
