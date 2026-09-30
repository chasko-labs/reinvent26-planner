"""Mock Amazon Web Services Events API for offline end-to-end tests.

Stdlib only. Mirrors the real shapes observed live (session `abbreviation`
and `sessionTime`, GetSchedule id lists, personal-time field names) so the
cli under test cannot tell it apart from the real thing:

    python mock/events_api.py --port 8499 --closed   # 409s like pre-8-Oct
    python mock/events_api.py --port 8499 --open     # gate flipped

Point the cli at it with EVENTS_API_BASE_URL plus any bearer token:

    EVENTS_API_BASE_URL=http://127.0.0.1:8499 EVENTS_ACCESS_TOKEN=test \\
        python -m reinvent26 reserve reinvent2026 <sessionId>

State (favorites, reservations, personal-time blocks) lives in memory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EVENT_ID = "reinvent2026"
GATE_MESSAGE = "reserved seating not open yet (api opens 8 Oct 2026)"


class MockState:
    def __init__(self, catalog: list, closed: bool = True):
        self.catalog = catalog
        self.by_id = {s.get("sessionId"): s for s in catalog
                      if isinstance(s, dict)}
        self.closed = closed
        self.favorites: list = []
        self.reserved: list = []
        self.personal_time: list = []
        self.blocks = 0


def _send(handler: BaseHTTPRequestHandler, status: int, payload) -> None:
    data = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length") or 0)
    if not length:
        return {}
    try:
        return json.loads(handler.rfile.read(length) or b"{}")
    except ValueError:
        return {}


def make_handler(state: MockState):
    class Handler(BaseHTTPRequestHandler):
        def _authed(self) -> bool:
            return bool(self.headers.get("Authorization"))

        def _guard_write(self) -> bool:
            if not self._authed():
                _send(self, 401, {"message": "Sign in to continue"})
                return False
            return True

        def _route(self):
            path = self.path.split("?", 1)[0]
            return re.fullmatch(r"/v1/events/([^/]+)(?:/(.*))?", path)

        def do_GET(self):  # noqa: N802
            m = self._route()
            if not m or m.group(1) != EVENT_ID:
                return _send(self, 404, {"message": "not found"})
            rest = (m.group(2) or "").rstrip("/")
            if rest == "sessions":
                return _send(self, 200, {"sessions": state.catalog})
            m2 = re.fullmatch(r"sessions/([^/]+)", rest)
            if m2:
                session = state.by_id.get(m2.group(1))
                if session is None:
                    return _send(self, 404, {"message": "unknown session"})
                return _send(self, 200, session)
            if rest == "schedule":
                return _send(self, 200, {"schedule": {
                    "favorites": list(state.favorites),
                    "reserved": list(state.reserved),
                    "personalTime": list(state.personal_time),
                }})
            if rest == "":
                return _send(self, 200, [{"eventId": EVENT_ID}])
            return _send(self, 404, {"message": "not found"})

        def do_POST(self):  # noqa: N802
            m = self._route()
            if not m or m.group(1) != EVENT_ID:
                return _send(self, 404, {"message": "not found"})
            rest = (m.group(2) or "").rstrip("/")
            if not self._guard_write():
                return
            body = _read_json(self)
            if rest == "favorites":
                return self._batch(state.favorites, body)
            if rest == "reservations":
                if state.closed:
                    return _send(self, 409, {"message": GATE_MESSAGE})
                return self._batch(state.reserved, body)
            if rest == "personal-time":
                return self._create_block(body)
            return _send(self, 404, {"message": "not found"})

        def _batch(self, store: list, body: dict):
            ids = body.get("sessionIds") or []
            ok, failed = [], []
            for sid in ids[:10]:
                if sid in state.by_id and sid not in store:
                    store.append(sid)
                    ok.append(sid)
                else:
                    failed.append(sid)
            return _send(self, 200, {"result": {"successful": ok,
                                               "failed": failed}})

        def _create_block(self, body: dict):
            for field in ("title", "description", "startDateTime",
                          "endDateTime"):
                if not body.get(field):
                    return _send(self, 400, {"message":
                        f"personalTime.{field} must not be null"})
            state.blocks += 1
            entry = {
                "personalTimeId": f"pt-{state.blocks}",
                "title": body["title"],
                "description": body["description"],
                "startDateTime": body["startDateTime"],
                "endDateTime": body["endDateTime"],
                "location": body.get("location") or "Personal",
            }
            state.personal_time.append(entry)
            return _send(self, 201, {})

        def do_PUT(self):  # noqa: N802
            m = self._route()
            rest = (m.group(2) or "").rstrip("/") if m else ""
            m2 = re.fullmatch(r"personal-time/([^/]+)", rest)
            if not m2 or not m or m.group(1) != EVENT_ID:
                return _send(self, 404, {"message": "not found"})
            if not self._guard_write():
                return
            body = _read_json(self)
            for i, entry in enumerate(state.personal_time):
                if entry["personalTimeId"] == m2.group(1):
                    state.personal_time[i] = {
                        "personalTimeId": entry["personalTimeId"],
                        "title": body.get("title", ""),
                        "description": body.get("description", ""),
                        "startDateTime": body.get("startDateTime", ""),
                        "endDateTime": body.get("endDateTime", ""),
                        "location": body.get("location"),
                    }
                    return _send(self, 200, {})
            return _send(self, 404, {"message": "unknown block"})

        def do_DELETE(self):  # noqa: N802
            m = self._route()
            rest = (m.group(2) or "").rstrip("/") if m else ""
            if not m or m.group(1) != EVENT_ID:
                return _send(self, 404, {"message": "not found"})
            if not self._guard_write():
                return
            m2 = re.fullmatch(r"(favorites|reservations)/([^/]+)", rest)
            if m2:
                kind, sid = m2.group(1), m2.group(2)
                if kind == "reservations" and state.closed:
                    return _send(self, 409, {"message": GATE_MESSAGE})
                store = (state.reserved if kind == "reservations"
                         else state.favorites)
                if sid in store:
                    store.remove(sid)
                    return _send(self, 200, {})
                return _send(self, 404, {"message": "already absent"})
            m3 = re.fullmatch(r"personal-time/([^/]+)", rest)
            if m3:
                before = len(state.personal_time)
                state.personal_time[:] = [
                    e for e in state.personal_time
                    if e["personalTimeId"] != m3.group(1)]
                if len(state.personal_time) < before:
                    return _send(self, 200, {})
                return _send(self, 404, {"message": "already absent"})
            return _send(self, 404, {"message": "not found"})

        def log_message(self, *a):
            pass

    return Handler


def load_sample_catalog() -> list:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "demo", "sessions-sample.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def start_server(catalog: list, port: int = 0,
                 closed: bool = True) -> ThreadingHTTPServer:
    state = MockState(catalog, closed=closed)
    server = ThreadingHTTPServer(("127.0.0.1", port),
                                 make_handler(state))
    server.mock_state = state  # type: ignore[attr-defined]
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8499)
    parser.add_argument("--catalog", default="",
                        help="sessions json (default: demo samples)")
    gate = parser.add_mutually_exclusive_group()
    gate.add_argument("--closed", dest="closed", action="store_true",
                      default=True, help="409 on reserve/cancel (default)")
    gate.add_argument("--open", dest="closed", action="store_false",
                      help="gate flipped: reserve works")
    args = parser.parse_args(argv)
    if args.catalog:
        with open(args.catalog, encoding="utf-8") as fh:
            catalog = json.load(fh)
    else:
        catalog = load_sample_catalog()
    server = start_server(catalog, port=args.port, closed=args.closed)
    print(f"# mock Events API on 127.0.0.1:{server.server_address[1]} "
          f"({'closed' if args.closed else 'open'})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
