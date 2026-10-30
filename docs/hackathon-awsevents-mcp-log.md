# hackathon log: awsevents mcp integration

## 2026-10-04 session 1

### goal

wire the aws events mcp server (api.awsevents.com/mcp) into the haunting stack so subagents can plan re:invent 2026 sessions through mcp tools.

### constraints

- rocm-aibox is headless linux. no browser.
- device-code grant not supported by the events api oauth endpoint (confirmed from docs).
- must use authorization code + pkce s256 with ssh tunnel for browser callback.
- tokens go to ssm parameter store (account 211125425201, namespace /heraldstack/shared/awsevents/*), never to local files.
- bridge launcher must be stdio on agent side, streamable http to api.awsevents.com/mcp, injecting bearer from ssm.
- mcp-transport-discipline: spawned agents only see stdio bindings.

### reference implementation

auth.py in cli/reinvent26/ has working pkce flow:

- opens browser to authorize url
- listens on 127.0.0.1:8484..8489/callback
- exchanges code for tokens
- stores to keychain or 0600 file (file storage NOT acceptable here)

### design decisions

#### token storage: ssm parameter store

- access token: /heraldstack/shared/awsevents/access-token (expires in 60 min)
- refresh token: /heraldstack/shared/awsevents/refresh-token (expires in 30 days, rotates on refresh)
- token expiry: /heraldstack/shared/awsevents/token-expires-at (unix timestamp)

ssm is the canonical storage per governance/secret-handling. no ~/.secrets, no .env, no local files.

#### login flow: ssh tunnel + browser on mac mini

1. bryan opens ssh tunnel from mac mini: `ssh -L 8484:localhost:8484 rocm-aibox`
2. on rocm-aibox: `awsevents-mcp-login` prints authorize url and listens on 127.0.0.1:8484
3. bryan opens url in browser on mac mini, signs in with builder id
4. callback arrives at localhost:8484 on mac mini, tunnels to rocm-aibox
5. login helper exchanges code for tokens, stores to ssm

#### bridge launcher: supergateway + ssm token fetch

- stdio on agent side via supergateway
- streamable http to https://api.awsevents.com/mcp
- bearer token fetched from ssm at each invocation (no caching in bridge)
- silent refresh when access token expired: fetch refresh token from ssm, call token endpoint, store new tokens

#### mcp transport

- settings/mcp.json uses ./mcp-launchers/run.sh (dispatcher pattern)
- run.sh finds the bridge script in heraldstack-mcp/launchers/bridges/
- registry.yaml entry documents the server

### implementation steps

1. create login helper: awsevents-mcp-login (python script using stdlib, stores to ssm)
2. create refresh helper: awsevents-mcp-refresh (silent refresh, called by bridge)
3. create bridge launcher: awsevents-bridge.sh (stdio -> streamable http, fetches token from ssm)
4. add registry.yaml entry
5. add mcp.json entry
6. create runbook at docs/runbooks/awsevents-mcp-login.md
7. test: bryan logs in, then call ListEvents through mcp

### what failed

- device code grant: not supported by the events api oauth endpoint. confirmed from docs at https://docs.aws.amazon.com/events/latest/devguide/mcp-server.html

### commands run

```bash
# checked hs-secret tool
which hs-secret && hs-secret --help

# read reference auth implementation
cat cli/reinvent26/auth.py

# read bridge patterns
cat ~/code/heraldstack/heraldstack-mcp/launchers/bridges/s3vectors-bridge.sh
cat ~/code/heraldstack/heraldstack-mcp/launchers/bridges/context7-bridge.sh

# read registry and mcp.json
cat ~/code/heraldstack/heraldstack-mcp/registry.yaml
cat ~/code/heraldstack/haunting-kiro-cli/.mcp.json
```

### files created

| file                                                                     | purpose                                           |
| ------------------------------------------------------------------------ | ------------------------------------------------- |
| bin/awsevents-mcp-login                                                  | login helper (tunnel-aware, stores tokens to ssm) |
| bin/awsevents-mcp-refresh                                                | silent token refresh (called by bridge)           |
| ~/code/heraldstack/heraldstack-mcp/launchers/bridges/awsevents-bridge.sh | stdio bridge to streamable http endpoint          |
| ~/code/heraldstack/heraldstack-mcp/docs/runbooks/awsevents-mcp-login.md  | runbook for bryan                                 |
| ~/code/heraldstack/heraldstack-mcp/registry.yaml                         | added awsevents entry                             |
| ~/code/heraldstack/haunting-kiro-cli/.mcp.json                           | added awsevents server entry                      |

### verified

- kiro-doctor check mcp-paths: pass (14 servers, all absolute launcher paths)
- python syntax: both helpers compile without errors
- bash syntax: bridge script passes `bash -n`
- supergateway: v3.4.3 available at ~/.nvm/versions/node/v24.14.0/bin/supergateway

### sign-in status

done 2026-10-29 20:25 utc via the ssh tunnel (see entries below). this section originally said "waiting on bryan", written before he signed in

## 2026-10-29 favorites, reservations, seat-aware re-plan

- favorited all 26 planned sessions. the first batch of 10 failed with code `other`, and an identical retry succeeded. `GET /schedule` confirms 26 favorites
- reserve attempt on the 16 reservable planned sessions: all `sessionFull`. seating opened 6 oct
- `seatAvailability` comes only from GetSession. fetched it for 252 topic sessions (666 s sequential): 171 unavailable, 75 walk-up or unknown, 5 veryLimited, 1 limited
- mapper is now seat-aware. it reads .cache/reinvent2026/seats.json, weights open seats 3x and unknown reservable 2x, and treats full sessions like walk-ups. the seat column shows "reserve (limited)", "full, walk-up line", and so on
- reserved CMP340 (amazon braket drug discovery and materials with q-ctrl, mon 13:00 mgm grand). `GET /schedule` shows 1 reserved
- 401 root cause: the shell exports AWS_PROFILE=ops-reader (read-only). refresh got a new token but could not store it, then returned None, so the next call went out without auth. fixed with AWSEVENTS_SSM_PROFILE (default aerospaceug-admin). the earlier ssm preflight and profile fixes had been lost in a subagent commit run and are re-applied
- local gate: added .githooks/pre-commit (py_compile helpers + pytest), linked as .git/hooks/pre-commit.local. the global hook chains to it, so every code commit runs the suite
- field notes with calls, code samples, enums, best practices, and lessons: docs/api-field-notes.md. redacted response samples: docs/samples/

## 2026-10-29 reserved-only plan: 15 seats booked

- bryan's rule: only sessions where we can hold a reserved seat. among those, rank workshops > chalk talks > breakouts. builders' sessions, labs, and code talks sit in between (26, 24, 18) by format similarity. topics only break ties
- pre-flight first: decoded the token (signed in, 37 min left), read the schedule in 3.4 s, then timed a 24-session probe: 13 s at 6 workers, 9 s at 12. only after that, the full sweep
- full sweep of 1484 reservable sessions in persisted chunks of 150 (.cache/reinvent2026/seats-sweep.json, resumable, hard timeout per chunk). the first 300-chunk took 90 s, the second 155 s, so chunks dropped to 150. no errors
- result: 1423 unavailable, 34 veryLimited, 20 limited, 7 available. 61 open seats across the conference: 24 workshops, 26 chalk talks, 0 breakouts. venues: mgm grand 28, wynn/encore 12, caesars palace 12, caesars forum 9
- mapper `reserved_only` mode: pool = held seats + open seats, bedrock/frontier still excluded. weight = format + half the topic weight + duration. held seats are fixed points (+1e6)
- booked 14 in one call, all successful, plus CMP340 from earlier. `GET /schedule`: 15 reserved
- the plan: mon mgm chalk talks (STG363, INV530-R1, CMP340, AIM433, STG338-R). tue wynn and caesars forum chalk talks (IND359-R1, IND322-R, IND3304-R1). wed workshops at mgm (ANT402-R, AIM434-R1) around INV537 at caesars forum. thu workshops (STG412 mgm, SEC401 wynn, MAM416 caesars palace). fri BIZ321-R1 workshop at wynn
- trade-off: none of the amazon leo anchors, open-weight, or self-managed-agent sessions had open seats. those topics now live only in the walk-up and interest lists
- lesson: the catalog's real constraint four weeks out is seats. venue logistics come second. a planner that ignores seatAvailability builds a schedule you cannot book

## 2026-10-29 booking push: gap analysis, swaps, fill command

- gap analysis: every one of the 46 open seats outside the plan overlapped a held seat or broke a venue gap. the sweep snapshot could not fill any window
- new command `python3 -m reinvent26 fill` (cli/reinvent26/fill.py):
  - reads the live schedule; held seats are fixed points
  - finds reservable sessions that fit free windows under the venue rules and live-checks only those
  - books by format priority
  - fails fast: no catalog or no token exits 2, a probe slower than 30 s exits 3, `--max-checks` caps the live calls
- dry run: 100 fitting candidates checked in about 16-20 s, 0 open. the gaps can only fill as people cancel
- swaps, applying workshop > chalk talk:
  - AIM318 (resilient vlm training on sagemaker hyperpod, mon 15:00-17:00 mgm, available) replaced AIM433 + STG338-R
  - SEC318-R1 (cryptographic computing, homomorphic encryption, tue 15:00-17:00 wynn, limited) replaced IND322-R + IND3304-R1
  - pattern: re-check the seat live, cancel, book, rebook the originals on failure. cancel returned true and booking succeeded both times
- schedule now: 13 reserved, 8 of them workshops. live fill pass after the swaps: 0 open
- daily-run reference (systemd user timer and cron) for other attendees: docs/daily-fill.md. not installed on bryan's host by his choice; he runs fill by hand

## 2026-10-29 book solid: week checks, re-sweep, rebalance, full-but-interesting

- checked the edges before ruling them out:
  - saturday 12-05 has no sessions
  - sunday 11-29 has 5 all-day non-reservable items: merch store, kiro galaxy run, datadog observaball, two event-service rooms
  - none of the 84 all-day or no-venue sessions is reservable
  - bookable days: mon to fri
- fresh full re-sweep of 1484 reservable sessions (10 chunks of about 55 s, no errors): 1425 unavailable, 32 veryLimited, 21 limited, 6 available
- `fill --rebalance` re-plans the week over held seats plus open seats, then swaps toward the target. it re-checks each seat live, cancels conflicts, books, and rebooks the originals on failure
- objective, first try: maximize reserved minutes. it wanted to trade CMP340 + AIM318 for a 4 h bootcamp, and SEC318-R1 for exam prep. 13 sessions would become 12, and formats outside bryan's ranking would come in. not run
- objective, second try: sessions first, then minutes, then format. it wanted to undo the workshop swaps (two chalk talks per window, same minutes). kept the workshops: same reserved time, no 30-minute hole, and workshops rank first
- every other open seat in the conference conflicts with a held seat. 13 reserved is the ceiling at current availability
- full but interesting (`python3 -m reinvent26 interest` -> docs/full-but-interesting.md):
  - 244 topic sessions without an open seat, each with presenters
  - 72 flagged for youtube after the event (breakouts, lightning talks, keynotes). chalk talks and workshops are not recorded
  - 354 presenters listed, sorted by session count, for following on social

## 2026-10-30 token resilience and code cleanup

- the in-session booking loop (bounded: 18 passes, 10 minutes apart, from a frozen git worktree at .cache/runner so code edits cannot break it mid-run) failed from pass 2 with "no valid token"
- root cause: the aerospaceug-admin sso session expired. the events api refresh token was fine (30 days), but the helper read and wrote ssm only through that sso profile
- fix in bin/awsevents-mcp-refresh:
  - reads fall back to ops-reader (iam roles anywhere, read-only, does not expire like sso)
  - when the write fails, the freshly refreshed access token is still used in memory, and the next run refreshes again
  - a rotated refresh token that cannot be stored is reported loudly. cognito has not rotated it so far
  - verified with sso expired: token valid, schedule read, fill dry run checked 100 fitting candidates, 0 open
- code cleanup, at bryan's request: verbose names, named constants, docstrings and comments everywhere
  - the first subagent pass was shallow
  - the second pass deleted four public functions from fill.py (fits, priority, window, ssm_token) while reporting "no behavior change". a module-attribute and ast diff against HEAD caught it
  - fill.py was rewritten by hand; the mapper, seats, and interest edits kept every function and stayed
- lesson: verify refactors mechanically (attribute presence, ast function sets, a dry run against the live api), not by the refactorer's summary
