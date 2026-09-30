"""Local-model ranking over a cached catalog (issue #10).

Optional natural-language pass: cached session JSON goes to an
OpenAI-compatible local endpoint, a ranked shortlist of session codes
comes back. The API/cache stays the source of truth — the model only
ranks, unknown codes are dropped. Access tokens are never accepted,
read, or sent here; only public cached catalog JSON is ranked.

Documented prompt lives in docs/local-models.md (PROMPT section) and is
mirrored by build_prompt().
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import time as dtime

DEFAULT_ENDPOINT = "http://127.0.0.1:8181/v1"
CHAT_PATH = "/chat/completions"

# "nothing before 9am", "not before 09:00", "after 9 am", "from 9am"
_NOT_BEFORE_RE = re.compile(
    r"(?:nothing\s+before|not\s+before|after|from|starts?\s+at)\s+"
    r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?",
    re.IGNORECASE,
)
_H24_RE = re.compile(
    r"(?:nothing\s+before|not\s+before|after|from)\s+(\d{1,2})(?::(\d{2}))?",
    re.IGNORECASE,
)


def parse_not_before(query: str) -> dtime | None:
    """Heuristic start-time floor parsed from a natural-language query."""
    m = _NOT_BEFORE_RE.search(query or "")
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        meridiem = m.group(3).lower()
        if meridiem == "p" and hour != 12:
            hour += 12
        if meridiem == "a" and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return dtime(hour, minute)
        return None
    m = _H24_RE.search(query or "")
    if m:
        hour, minute = int(m.group(1)), int(m.group(2) or 0)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return dtime(hour, minute)
    return None


def filter_not_before(sessions: list, floor: dtime | None) -> list:
    """Drop sessions starting before the floor; timeless items are kept.

    Delegates to schedule.filter_by_time so the comparison lives in one
    place; rank keeps only the natural-language floor parsing.
    """
    if floor is None:
        return list(sessions)
    from reinvent26 import schedule as _sched

    return _sched.filter_by_time(sessions, not_before=floor.strftime("%H:%M"))


def compact_session(s: dict) -> dict:
    code = s.get("code") or s.get("sessionId", "?")
    return {
        "code": code,
        "title": s.get("title", "?"),
        "level": s.get("level", "?"),
        "topics": s.get("topics", []),
        "startTime": s.get("startTime", "?"),
        "abstract": str(s.get("abstract", s.get("description", "")))[:300],
    }


def build_prompt(query: str, sessions: list, top: int) -> tuple:
    """Return (system, user) prompt strings. Kept in sync with the doc."""
    system = (
        "You rank reinvent session catalogs. Reply with JSON only: "
        '{"picks": [{"code": "<SESSION CODE>", "reason": "<one line>"}]}. '
        f"Rank at most {top} sessions, best first. "
        "Use only codes from the catalog below; never invent codes."
    )
    lines = [f"request: {query}", "", "catalog (code | title | level | start | topics):"]
    for s in sessions:
        c = compact_session(s if isinstance(s, dict) else {})
        topics = ",".join(str(t) for t in c["topics"]) if isinstance(c["topics"], list) else str(c["topics"])
        lines.append(
            f"{c['code']} | {c['title']} | {c['level']} | {c['startTime']} | {topics}"
        )
    user = "\n".join(lines)
    return system, user


def _extract_json(text: str):
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def parse_picks(raw_text: str, sessions: list, top: int) -> list:
    """Validate model output against the catalog; drop unknown codes.

    Returns catalog session dicts in model-ranked order, deduplicated.
    """
    by_code = {}
    for s in sessions:
        if not isinstance(s, dict):
            continue
        code = s.get("code") or s.get("sessionId")
        if code:
            by_code[str(code).lower()] = s
    data = _extract_json(raw_text or "")
    items = []
    if isinstance(data, dict):
        items = data.get("picks", [])
    elif isinstance(data, list):
        items = data
    if not isinstance(items, list):
        return []
    out, seen = [], set()
    for item in items:
        code = item if isinstance(item, str) else (item or {}).get("code", "")
        key = str(code).strip().lower()
        if not key or key in seen or key not in by_code:
            continue
        seen.add(key)
        out.append(by_code[key])
        if len(out) >= top:
            break
    return out


def rank_via_model(
    query: str,
    sessions: list,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = "local",
    top: int = 10,
    timeout: int = 120,
) -> list:
    """POST cached sessions + query to a local OpenAI-compat endpoint.

    Never sends credentials: no token argument exists on purpose.
    """
    system, user = build_prompt(query, sessions, top)
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        }
    ).encode()
    url = (endpoint or DEFAULT_ENDPOINT).rstrip("/") + CHAT_PATH
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode() or "{}")
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"unexpected model response shape: {str(payload)[:200]}") from e
    picks = parse_picks(content, sessions, top)
    if not picks:
        raise RuntimeError(f"model returned no catalog codes: {content[:200]}")
    return picks
