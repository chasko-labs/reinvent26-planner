# events api field notes: calls, samples, best practices, lessons learned

everything here was observed against the live api on 2026-10-29 with a signed-in builder id. redacted response samples live in docs/samples/. companion pages: docs/event-map.md, docs/launch-ledger.md, docs/hackathon-awsevents-mcp-log.md

## surface used

| capability          | call                                                                      | used for                                     | observed                               |
| ------------------- | ------------------------------------------------------------------------- | -------------------------------------------- | -------------------------------------- |
| list events         | `GET /v1/events`                                                          | find `reinvent2026`                          | works                                  |
| list sessions       | `GET /v1/events/{eventId}/sessions?includeAbstracts=true&nextToken=...`   | full catalog, 2350 sessions                  | works, paginate until no nextToken     |
| get session         | `GET /v1/events/{eventId}/sessions/{sessionId}`                           | `seatAvailability` (list does not return it) | ~2.6 s per call sequential             |
| favorite            | `POST /v1/events/{eventId}/favorites` body `{"sessionIds":[...]}`         | 26 planned sessions                          | batches of 10, per-item results        |
| schedule            | `GET /v1/events/{eventId}/schedule`                                       | confirm favorites, reserved, personal time   | source of truth after writes           |
| reserve             | `POST /v1/events/{eventId}/reservations` body `{"sessionIds":[...]}`      | reserved-seat plan                           | per-item results, `sessionFull` common |
| cancel / unfavorite | `DELETE .../reservations/{sessionId}`, `DELETE .../favorites/{sessionId}` | re-plan                                      | not exercised yet                      |

openapi: `https://api.awsevents.com/v1/openapi.json` (cached at .cache/openapi.json)

## code samples

paginate the catalog (cli/reinvent26/api.py)

```python
def iter_sessions(event_id, token=None, include_abstracts=False, page_size=100):
    next_token = None
    while True:
        page = read_with_retry(_request, "GET", f"/v1/events/{event_id}/sessions", token=token,
                               params={"includeAbstracts": str(include_abstracts).lower(),
                                       "maxResults": page_size, "nextToken": next_token})
        yield from page.get("items") or page.get("sessions") or []
        next_token = page.get("nextToken")
        if not next_token:
            return  # a short page is not the last page; only a missing nextToken is
```

bulk write, then read back (favorites and reservations share the shape)

```python
res = api.favorite_sessions("reinvent2026", tok, ids)   # batches of 10
failed = [f for b in res for f in b["result"]["failed"]]
retry = [f["sessionId"] for f in failed if f["code"] == "other"]
if retry:
    api.favorite_sessions("reinvent2026", tok, retry)   # "other" cleared on the second try
sched = api.get_schedule("reinvent2026", tok)["schedule"]  # {"favorites": [...], "reserved": [...], "personalTime": [...]}
```

response shape (docs/samples/reserve-response.json, ids only)

```json
[
  {
    "result": {
      "failed": [{ "code": "sessionFull", "sessionId": "..." }],
      "successful": []
    }
  }
]
```

seat-aware planning: availability only comes from GetSession, so fetch it for the topic pool and persist

```python
seats = {}
for code in pool_codes:
    s = api.get_session("reinvent2026", catalog[code]["sessionId"], token=tok)
    seats[code] = (s.get("session") or s).get("seatAvailability")
# persisted to .cache/reinvent2026/seats.json with fetched_at; the mapper weights open seats 3x
```

token handling: the access token lives 60 minutes, so read it through the refresh helper every time

```python
tok = refresh_helper.get_valid_access_token()  # reads ssm, refreshes when expired, rotates and stores
```

## enums worth knowing

| enum             | values                                                                                                                                       |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| BulkFailureCode  | sessionNotReservable, scheduleConflict, alreadyScheduled, sessionFull, insufficientAccess, timePassed, alreadyFavorited, notFavorited, other |
| SeatAvailability | available, limited, veryLimited, unavailable, walkUp                                                                                         |

## best practices

- treat http 200 on a bulk write as "request accepted", not "every item succeeded". read `result.failed` per item, then confirm with `GET /schedule`
- retry `other` once. it cleared on retry in our run. never retry `sessionFull`; re-plan around it instead
- `seatAvailability` is missing from the list call. fetch it per session for a short list, persist it with a timestamp, and refresh before booking
- plan before you book: schedule first (venue gaps, anchors, topic weights), then reserve only what the plan keeps. the plan stays the source of intent, the api schedule stays the source of truth
- keep the catalog on disk (.cache/reinvent2026/catalog.json) and re-pull daily. rooms and times move
- tokens: authorization code plus pkce only, no device code. on a headless host, tunnel the loopback callback over ssh. keep tokens in a secrets store, never on disk or in logs
- use a dedicated env var for the secrets-store profile (`AWSEVENTS_SSM_PROFILE`). a shell-wide `AWS_PROFILE` silently overrode ours with a read-only role

## lessons learned (the honest list)

| lesson                            | what happened                                                                                                                                                                               | fix                                                                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| seats go fast                     | on 2026-10-29 all 16 reservable sessions in the first plan returned `sessionFull`. a full sweep of 1484 reservable sessions found 61 with seats (24 workshops, 26 chalk talks, 0 breakouts) | reserved-only mode on the sweep; booked 15 seats, all confirmed                                                                        |
| verify before long runs           | a long sweep started without checking the token or timing a sample                                                                                                                          | pre-flight: decode the token, read the schedule, time a 24-session probe, then sweep in persisted, resumable chunks with hard timeouts |
| silent refresh failure            | refresh got a new token from oauth, then the ssm write failed under a read-only profile. the helper returned None, so the next call went out without a token: 401 "Sign in to continue"     | dedicated profile variable, and surface the store error instead of swallowing it                                                       |
| first bulk batch failed           | the first favorites batch of 10 came back all `other`. an identical retry succeeded                                                                                                         | retry `other` once, then confirm via schedule                                                                                          |
| list vs get fields differ         | `seatAvailability` appears only on GetSession                                                                                                                                               | per-session fetch for the shortlist                                                                                                    |
| sequential gets are slow          | 252 GetSession calls took 666 s                                                                                                                                                             | next: bounded concurrency with 429-aware backoff; check docs quotas first                                                              |
| test fixtures clobbered real data | a test wrote a 4 kb synthetic catalog over the real snapshot and the generated docs                                                                                                         | tests use tmp_path only; mapper refuses to run under pytest without --out-dir                                                          |
| filter order matters              | untagged sessions leaked into the watch list and excluded tables (about 1500 rows) because exclusion ran before the topic filter                                                            | filter on topic first                                                                                                                  |
| keyword regexes overreach         | "riot" matched "marriott"; "self-managed" matched kubernetes and oltp                                                                                                                       | word boundaries; require agent context                                                                                                 |
| no ephemeral state                | early prototypes lived in /tmp and nearly got lost                                                                                                                                          | everything persists in the repo or .cache/                                                                                             |

## open

- cancel and unfavorite paths not yet exercised against the live api
- the mcp server path (`https://api.awsevents.com/mcp`) not yet exercised end to end; the rest api carried this pass
- watch `veryLimited` sessions that fit the plan: SEC401 (thu 12:00 wynn/encore), CMP408 (mon 13:30 mgm, overlaps CMP340), AIM3304 (wed 15:00 mgm, overlaps the NET341 anchor)
