"""Pure schedule logic: clash detection, free-slot search, topic matching.

All functions are pure (no network) so they stay unit-testable.
Session dicts follow the Events API shape: sessionId/code, title, level,
tracks, topics, services, startTime/endTime (ISO strings).
"""

from __future__ import annotations

from datetime import datetime, timedelta


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


def _text_fields(s: dict) -> str:
    parts = [s.get("title", "")]
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
    code = s.get("code") or s.get("sessionId", "?")
    return (
        f"{code} | {s.get('title', '?')} | {s.get('level', '?')} | "
        f"{s.get('startTime', '?')}->{s.get('endTime', '?')} | "
        f"{s.get('room', '?')}"
    )
