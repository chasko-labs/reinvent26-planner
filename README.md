# reinvent26-attendee-planner

A Python command-line interface (CLI) for re:Invent 2026 session discovery, planning, and seat booking. It talks to the public Events API (application programming interface). The project uses only the Python standard library, so there is nothing to install.

Premise: an AI-free re:Invent. Deterministic code plans the week; models only rank and explain. The living output is https://bryanchasko.com/reinvent26. Bring your own topics: every example below uses mine, and the defaults in `data/reinvent2026/map-config.json` are mine too. Replace them with yours.

## prerequisites

You must have Python 3.10 or newer. You check with:

```bash
python3 --version
```

macOS ships no `python` command. You must type `python3`, not `python`. If your Mac has no Python 3 at all, install it with `brew install python` and re-run the check.

You must clone the live repo. A stale repo with a similar name exists, and it will never catch up:

```bash
git clone git@github.com:chasko-labs/reinvent26-attendee-planner.git reinvent26-planner
cd reinvent26-planner/cli
```

## quick start

You run every command from the `cli/` directory. You start each session by checking your sign-in state:

```bash
# report sign-in state, api reachability, schedule readability
python3 -m reinvent26 status reinvent2026
```

You sign in when `status` says you are signed out:

```bash
python3 -m reinvent26 login
```

The command prints a URL. You open it in your browser and sign in with your Builder ID (AWS identity for builders). The full recipe lives in [docs/sign-in.md](docs/sign-in.md). That doc covers the Python check and the Mac recipe. It shows how to tell if you are signed in. It explains what each error means. Read it first if `status` confuses you.

You then walk the happy path in order:

```bash
# list events, no sign-in needed
python3 -m reinvent26 events

# pull the full catalog, cached
python3 -m reinvent26 sessions reinvent2026

# rank by topic keywords (mine shown; substitute yours)
python3 -m reinvent26 shortlist reinvent2026 --topics leo,braket --level 3

# show your schedule plus double bookings
python3 -m reinvent26 schedule reinvent2026

# list sessions fitting a free window with no clash
python3 -m reinvent26 slots reinvent2026 --window 2026-12-01T13:00:00,2026-12-01T16:00:00

# preview what fits, then book
python3 -m reinvent26 fill --dry-run
python3 -m reinvent26 fill
```

You can preview the whole loop without signing in. The command `python3 -m reinvent26 events` needs no token. The script `python3 demo/demo_public.py` replays a recorded session end to end.

## commands

Each command does one thing. The table lists every command with its one-line job:

| command              | description                                                |
| -------------------- | ---------------------------------------------------------- |
| `login`              | sign in with Builder ID (PKCE, loopback callback)          |
| `status`             | show sign-in state, api reachability, schedule readability |
| `events`             | list current/upcoming events                               |
| `sessions`           | list catalog pages until no nextToken                      |
| `shortlist`          | rank sessions by topic keywords                            |
| `schedule`           | show schedule plus double bookings                         |
| `slots`              | list sessions fitting free windows with no clash           |
| `favorite`           | favorite up to 10 session ids per call                     |
| `block`              | create a personal-time block                               |
| `reblock`            | replace every field of a personal-time block               |
| `unblock`            | delete a personal-time block                               |
| `remove-favorite`    | remove one favorite                                        |
| `cancel-reservation` | cancel one reservation                                     |
| `stack-pick`         | stack-aware shortlist from live resources                  |
| `rank`               | rank cached catalog via local model                        |
| `ingest`             | load curated sessions into cache                           |
| `reserve`            | reserve seats                                              |
| `fill`               | book open seats into free windows of the live schedule     |
| `interest`           | write full-but-interesting page with presenters to follow  |
| `map`                | build event map and launch ledger from catalog             |
| `new-sessions`       | diff the live catalog, evaluate new sessions, report       |
| `find-me`            | render a shareable find-bryan page from the live schedule  |

PKCE means Proof Key for Code Exchange. It is the browser sign-in flow the Events API requires. You never handle its secrets by hand.

## events mcp

The same Events API is available as the AWS Events MCP server at `https://api.awsevents.com/mcp`. MCP means Model Context Protocol. It carries the same operations over streaming HTTP (hypertext transfer protocol) for AI assistants. This repo does not ship its own MCP server. The CLI above is the scriptable interface. The MCP server is the interactive one. Both follow the rules in [skills/awsevents-muse/SKILL.md](skills/awsevents-muse/SKILL.md) — that skill is the shared rulebook, so read it before driving either interface.

You follow five rules with either interface:

1. Sign in with your Builder ID first. The sign-in uses PKCE with a loopback callback. It lands on `127.0.0.1:8484` on your own machine. Your access token lasts 60 minutes. Your refresh token lasts 30 days.
2. Expect sign-in on every MCP tool call, including catalog reads. The REST interface differs here: public `ListEvents` needs no token.
3. Pull the catalog the cheap way. You request `ListSessions` with `includeAbstracts=false`. You follow `nextToken` until it is absent. A short page is not the last page. You shortlist locally. You call `GetSession` for abstracts and `seatAvailability` on the shortlist only.
4. Treat favorites as interest, not seats. You reserve 1 to 10 ids per call. You never trust an HTTP 200 on a batch. You inspect each per-session result. You confirm with `GetSchedule`.
5. Never blind-resend an unknown write outcome. You read the schedule. You compare it with your intent. You submit only what remains. A 404 on cancel or remove means already absent, so you treat it as complete.

You use the server from another assistant through a per-assistant guide. Each guide gives the exact config for that assistant and nothing else:

- [kiro-cli](docs/integrations/kiro-cli.md)
- [Meta Muse](docs/integrations/meta-muse.md)
- [Microsoft Copilot](docs/integrations/copilot.md)
- [Google Gemini](docs/integrations/gemini.md)

You read the call-by-call record in [docs/mcp-approach.md](docs/mcp-approach.md). It shows the live schedule state. It gives the exact MCP walkthrough order. You read enums and hard-won lessons in [docs/api-field-notes.md](docs/api-field-notes.md). It lists every result code. It records what actually happened against the live API.

## architecture

The tree mirrors the commands. Each file owns one job:

```
cli/reinvent26/
  __main__.py     # entry point
  cli.py          # argparse scaffolding, 22 subcommands
  api.py          # Events API client (stdlib only)
  auth.py         # Builder ID OAuth with PKCE, keychain/file storage
  cache.py        # .cache/<eventId>/ caching layer
  mapper.py       # topic tagging, venue travel gaps, exclusion rules
  rank.py         # session ranking by format, topic, duration
  schedule.py     # schedule normalization, clash detection
  seats.py        # seat availability sweeping
  fill.py         # book open seats into free windows
  interest.py     # full-but-interesting page generator
  newevents.py    # daily new-session diff, local-model eval, report + handoff
  findme.py       # shareable find-bryan page from live schedule
  inventory.py    # catalog dump to json for debugging
  seeds.py        # re:invent 2026 topic/venue defaults
  seeds.json      # curated session count targets
data/reinvent2026/
  *.json          # curated session lists by lens
  map-config.json # venue gaps, format weights, topic weights, exclusions
demo/
  demo_public.py           # public api demo
  sessions-sample.json     # sample ListSessions response
  schedule-sample.json     # sample GetSchedule response
docs/
  api-field-notes.md       # api calls, enums, lessons learned
  data-schema.md           # session schema and ingest layout
  event-map.md             # venue map with travel times
  launch-ledger.md         # session launch order and notes
  mcp-approach.md          # mcp vs cli sign-in patterns
  local-models.md          # local model setup for rank command
  samples/                 # api response shapes
tests/
  test_*.py                # pytest unit tests
skills/
  awsevents-muse/
    SKILL.md               # MCP skill definition
rust/
  catalog-filter/          # optional rust filter for fast catalog scan
```

## data files

Curated session lists live in `data/reinvent2026/*.json`. Each file groups sessions by interest lens. You read the schema in [docs/data-schema.md](docs/data-schema.md) — it defines the session shape and the ingest layout before you add a file.

## tests

You run the suite with:

```bash
python3 -m pytest -q
```

## contributing gate

You enable the pre-push hook once per clone:

```bash
git config core.hooksPath .githooks
```

The hook runs a secret-shape scan, compile, pytest, and the offline demo. You must see all four pass before you push.

## docs

Each doc answers one question. You start with `sign-in.md` and branch from there:

- [docs/sign-in.md](docs/sign-in.md) — how to tell if you are signed in, the Mac recipe, token lifetimes, and what each error means. Read this first when anything fails.
- [docs/hallway-windows.md](docs/hallway-windows.md) — breakfast, lunch, dinner, and morning/midday/evening meetup slots. Read this to find Bryan between sessions.
- [docs/daily-new-sessions.md](docs/daily-new-sessions.md) — the watcher runbook: new-session diffs, local-model eval, and cron setup. Read this to automate the morning report.
- [docs/roadmap.md](docs/roadmap.md) — planned work, ordered by value over effort. Read this before proposing a feature.
- [docs/hackathon-entry.md](docs/hackathon-entry.md) — the Builder Center post draft: what, why, API use, setup, demo script. Read this to publish the entry.
- [docs/integrations/kiro-cli.md](docs/integrations/kiro-cli.md) — kiro-cli install, MCP config, and watcher handoff. Read this to drive the API from kiro-cli.
- [docs/integrations/meta-muse.md](docs/integrations/meta-muse.md) — Meta Muse custom connector, verified limits, and the report-paste pattern. Read this to use Muse with the planner.
- [docs/integrations/copilot.md](docs/integrations/copilot.md) — the Copilot routes that can reach the server. Read this to pick your Copilot path.
- [docs/integrations/gemini.md](docs/integrations/gemini.md) — Gemini web app and Gemini CLI. Read this to use Gemini with the planner.
- [docs/mcp-approach.md](docs/mcp-approach.md) — MCP versus CLI sign-in patterns and live schedule state. Read this for the call-by-call record.
- [docs/event-map.md](docs/event-map.md) — venue map with travel times. Read this to plan walks between venues.
- [docs/launch-ledger.md](docs/launch-ledger.md) — sessions signaling new launches, regenerated from the catalog. Read this to spot announcements.
- [docs/daily-fill.md](docs/daily-fill.md) — seat-filling runbook. Read this to book released seats by hand.
- [docs/api-field-notes.md](docs/api-field-notes.md) — API calls, enums, and lessons learned. Read this before debugging any API surprise.

## license

MIT
