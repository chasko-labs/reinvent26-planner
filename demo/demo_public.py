"""Public-reads demo: runs with no token and no network.

Uses checked-in cached samples only. Exercises the same pure schedule
logic the live CLI uses: shortlist, clash check, open-slot finder, and
stack-aware keyword mapping.

Run: python demo/demo_public.py
No EVENTS_ACCESS_TOKEN is read or required. No tokens are printed.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26.schedule import (  # noqa: E402
    find_clashes,
    find_open_slots,
    match_topics,
    stack_keywords,
    summarize,
)

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))


def load(name: str):
    with open(os.path.join(DEMO_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    sessions = load("sessions-sample.json")
    scheduled = load("schedule-sample.json")

    print(f"# loaded {len(sessions)} cached sessions, {len(scheduled)} scheduled items (no token, no network)")

    print("\n## shortlist: topics=agents,mcp,bedrock level=300/400 top=3")
    ranked = match_topics(sessions, ["agents", "mcp", "bedrock"])
    ranked = [s for s in ranked if str(s.get("level", "")).startswith(("3", "4"))]
    for s in ranked[:3]:
        print(summarize(s))

    print("\n## schedule with clash check")
    for item in scheduled:
        print(summarize(item))
    clashes = find_clashes(scheduled)
    if clashes:
        for a, b in clashes:
            print(f"# clash: {a.get('code')} x {b.get('code')}")
    else:
        print("# no double bookings")

    print("\n## open slots: window 2026-12-01T13:00:00 to 2026-12-01T16:00:00")
    print("# baseline is clash-free (ANT301 + SRV301); CON401 excluded because it clashes above")
    windows = [{"start": "2026-12-01T13:00:00", "end": "2026-12-01T16:00:00"}]
    baseline = [scheduled[0], scheduled[2]]
    for s in find_open_slots(sessions, windows, baseline):
        print(summarize(s))

    print("\n## stack-aware pick: Lambda + DynamoDB footprint")
    kws = stack_keywords([{"service": "AWS::Lambda::Function"}, {"service": "Amazon DynamoDB"}])
    print("# keywords: " + ", ".join(kws))
    for s in match_topics(sessions, kws)[:2]:
        print(summarize(s))

    print("\n# demo complete: favorite now, reserve after 8 Oct 2026, confirm every write with GetSchedule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
