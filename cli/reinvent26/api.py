"""Minimal REST client for the Amazon Web Services Events API.

Uses only the standard library so the cli runs anywhere with python 3.11+.
Auth: Bearer access token from the Builder ID OAuth PKCE flow (see docs/).
Public reads (ListEvents, and ListSessions for events that do not require
registration) work without a token. All schedule writes need token +
event registration.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

BASE_URL = "https://api.awsevents.com"
OPENAPI_URL = "https://api.awsevents.com/v1/openapi.json"


class EventsError(Exception):
    def __init__(self, status: int, message: str, retry_after: float | None = None):
        super().__init__(f"http {status}: {message}")
        self.status = status
        self.retry_after = retry_after


def _request(
    method: str,
    path: str,
    token: str | None = None,
    params: dict | None = None,
    body: dict | None = None,
) -> dict | list:
    url = BASE_URL + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()[:500]
        except Exception:
            detail = ""
        retry_after = None
        if e.code == 429:
            try:
                retry_after = float(e.headers.get("Retry-After", "5"))
            except ValueError:
                retry_after = 5.0
        raise EventsError(e.code, detail or e.reason, retry_after) from e


def _sleep(seconds: float) -> None:
    """Sleep hook (module-level so tests can record instead of waiting)."""
    time.sleep(seconds)


def write_with_retry_429(fn, *args, **kwargs):
    """Writes: one retry honoring Retry-After on 429 only.

    429 means throttled before processing, so one retry is safe. 500/503
    or timeouts on writes never blind-retry: reconcile via get_schedule
    and submit only what remains. Delete operations (cancel/remove) are
    exempt: they retry once on 500/503 because 404 on retry means
    already-complete.
    """
    try:
        return fn(*args, **kwargs)
    except EventsError as e:
        if e.status == 429:
            _sleep(e.retry_after or 5.0)
            return fn(*args, **kwargs)
        raise


def delete_with_retry(fn, *args, **kwargs):
    """Deletes: like writes, plus one retry on 500/503 (idempotent)."""
    try:
        return write_with_retry_429(fn, *args, **kwargs)
    except EventsError as e:
        if e.status in (500, 503):
            return fn(*args, **kwargs)
        raise


def read_with_retry(fn, *args, **kwargs):
    """Reads: honor Retry-After on 429, back off on 500/503.

    Retries 429 twice (sleeping each Retry-After) and 500/503 twice
    (sleeping 1s then 2s). Never retries 403/404/409: 403 with a body
    means not registered, and retrying will not fix it.
    """
    delay = 1.0
    for attempt in range(3):
        try:
            return fn(*args, **kwargs)
        except EventsError as e:
            if e.status == 429 and attempt < 2:
                _sleep(e.retry_after or 5.0)
                continue
            if e.status in (500, 503) and attempt < 2:
                _sleep(delay)
                delay *= 2
                continue
            raise


def list_events(include_past: bool = False) -> list:
    params = {"includePast": "true"} if include_past else None
    out = _request("GET", "/v1/events", params=params)
    if isinstance(out, dict):
        for key in ("events", "items", "data"):
            if isinstance(out.get(key), list):
                return out[key]
        return [out]
    return out


def iter_sessions(
    event_id: str,
    token: str | None = None,
    include_abstracts: bool = False,
    locale: str | None = None,
    page_size: int = 100,
) -> object:
    """Yield every session in the catalog.

    Follows nextToken until absent. A short page is not the last page.
    First pass callers should use include_abstracts=False for speed,
    then fetch abstracts for the shortlist only.
    """
    next_token = None
    while True:
        params = {
            "includeAbstracts": "true" if include_abstracts else "false",
            "locale": locale,
            "maxResults": page_size,
            "nextToken": next_token,
        }
        page = read_with_retry(
            _request,
            "GET",
            f"/v1/events/{event_id}/sessions",
            token=token,
            params=params,
        )
        if isinstance(page, dict):
            sessions = page.get("sessions") or page.get("items") or []
            for s in sessions:
                yield s
            next_token = page.get("nextToken")
        elif isinstance(page, list):
            for s in page:
                yield s
            next_token = None
        else:
            return
        if not next_token:
            return


def get_session(event_id: str, session_id: str, token: str | None = None) -> dict:
    return read_with_retry(
        _request,
        "GET",
        f"/v1/events/{event_id}/sessions/{session_id}",
        token=token,
    )


def get_schedule(event_id: str, token: str) -> dict:
    """Source of truth for the attendee schedule. Use to confirm writes."""
    return read_with_retry(
        _request, "GET", f"/v1/events/{event_id}/schedule", token=token
    )


def _batched(ids: list, size: int = 10):
    for i in range(0, len(ids), size):
        yield ids[i : i + size]


def favorite_sessions(event_id: str, token: str, session_ids: list) -> list:
    """Favorite in batches of 10. Returns per-batch responses.

    Inspect each per-session result: http 200 does not mean every item
    succeeded. Confirm final state with get_schedule.
    """
    if not 1 <= len(session_ids) <= 1000:
        raise ValueError("need at least 1 session id")
    out = []
    for batch in _batched(list(dict.fromkeys(session_ids))):
        out.append(
            write_with_retry_429(
                _request,
                "POST",
                f"/v1/events/{event_id}/favorites",
                token=token,
                body={"sessionIds": batch},
            )
        )
    return out


def reserve_sessions(event_id: str, token: str, session_ids: list) -> list:
    """Reserve in batches of 10. Same per-session inspection rule as favorites.

    Before 8 Oct 2026 reserving returns 409 (operation closed). Treat 409
    as retry-after-reopen, not a malformed request.
    """
    out = []
    for batch in _batched(list(dict.fromkeys(session_ids))):
        out.append(
            write_with_retry_429(
                _request,
                "POST",
                f"/v1/events/{event_id}/reservations",
                token=token,
                body={"sessionIds": batch},
            )
        )
    return out


def _delete_once(method: str, path: str, token: str) -> bool:
    """One DELETE with idempotent retry. True when removed, False on 404."""
    try:
        delete_with_retry(_request, method, path, token=token)
    except EventsError as e:
        if e.status == 404:
            return False
        raise
    return True


def cancel_reservation(event_id: str, token: str, session_id: str) -> bool:
    """Cancel one reservation. True when removed, False when already absent.

    404 means already absent (complete on retry). Retried once on
    500/503 (idempotent); other failures raise so the caller can
    reconcile via get_schedule before deciding.
    """
    return _delete_once(
        "DELETE", f"/v1/events/{event_id}/reservations/{session_id}", token
    )


def remove_favorite(event_id: str, token: str, session_id: str) -> bool:
    """Remove one favorite. True when removed, False when already absent."""
    return _delete_once(
        "DELETE", f"/v1/events/{event_id}/favorites/{session_id}", token
    )


def add_personal_time(
    event_id: str,
    token: str,
    title: str,
    start: str,
    end: str,
    description: str = "",
    location: str | None = None,
) -> None:
    """Timestamps are UTC YYYY-MM-DDTHH:mm:ss without Z, seconds 00, end after
    start, whole 5-minute duration. Create returns no body; read the new id
    back from get_schedule."""
    from reinvent26.schedule import validate_personal_time

    validate_personal_time(title, start, end)
    body = {
        "title": title,
        "description": description,
        "startDateTime": start,
        "endDateTime": end,
    }
    if location:
        body["location"] = location
    write_with_retry_429(
        _request,
        "POST",
        f"/v1/events/{event_id}/personal-time",
        token=token,
        body=body,
    )


def replace_personal_time(
    event_id: str,
    token: str,
    block_id: str,
    title: str,
    start: str,
    end: str,
    description: str = "",
    location: str | None = None,
) -> None:
    """Replace every field of a personal-time block.

    Omitting location sends an explicit null, which clears it.
    """
    from reinvent26.schedule import validate_personal_time

    validate_personal_time(title, start, end)
    body = {
        "title": title,
        "description": description,
        "startDateTime": start,
        "endDateTime": end,
        "location": location,
    }
    write_with_retry_429(
        _request,
        "PUT",
        f"/v1/events/{event_id}/personal-time/{block_id}",
        token=token,
        body=body,
    )


def delete_personal_time(event_id: str, token: str, block_id: str) -> bool:
    """Delete a personal-time block. True when removed, False when already
    absent (404)."""
    return _delete_once(
        "DELETE", f"/v1/events/{event_id}/personal-time/{block_id}", token
    )


