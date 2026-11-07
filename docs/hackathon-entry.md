# hackathon entry draft: re:Invent attendee planner

paste-ready draft for the AWS Builder Center project post. repo link,
setup, and demo point at this repo. nothing here is published until
bryan posts it.

## title

re:Invent attendee planner — CLI, nightly watcher, and find-me pages on the Events API and MCP

## what I built

a stdlib-only python CLI with 22 commands covering all 12 Events API
operations: catalog pull, shortlist, venue-gap slots, seat sweeps,
favorites, reservations, personal-time blocks, launch ledger, and
re-runnable fill plans. on top of it:

- a nightly watcher that diffs the catalog, evaluates new sessions
  with a local model, flags launch signals, and writes a report ending
  in a handoff prompt for kiro-cli over the Events MCP server.
- `find-me` pages: held seats, morning/midday/evening windows, week
  topics, and a visitor question picked by event day. built so other
  builders can find bryan for breakfast, lunch, dinner, and re:Play.
- a public week page generated from the live schedule: full-day
  timelines (sessions, transit legs, breakfast/lunch/dinner blocks,
  open windows), seats-now grouped by live seat band, per-venue
  close-up maps and a monorail strip rendered from real map tiles,
  hallway rules, and floor-photo strips packed per a deterministic
  collage recipe. every map dot is numbered to its session row.
- MCP integration guides for four assistants (kiro-cli, Meta Muse,
  Copilot, Gemini), each verified against the live server — including
  the documented dead end where Meta's hosted OAuth callback is
  rejected, with the exact `redirect_mismatch` evidence.

## why

2,400+ sessions across five Strip venues cannot be held in a head.
the same failure repeats every year: favorited sessions that clash,
back-to-backs across the Strip that cannot be walked, and full
workshops with no backup plan. this planner turns the catalog into a
week that fits: venue gaps enforced in code, scarcity-first booking,
and a morning report of what changed overnight.

## how it uses the API and MCP server

all 12 REST operations, each bound to a command:

| operation                                                  | used by                                           |
| ---------------------------------------------------------- | ------------------------------------------------- |
| ListEvents, GetEvent                                       | `events`, `status` (reachability, name, timezone) |
| ListSessions, GetSession                                   | `sessions`, seat sweeps, watcher enrichment       |
| GetSchedule                                                | `schedule`, every write confirmed against it      |
| AssociateFavorites, DisassociateFavorite                   | `favorite`, `remove-favorite`, watcher handoff    |
| ReserveSessions, CancelReservation                         | `reserve`, `fill` with rebook rollback            |
| CreatePersonalTime, UpdatePersonalTime, DeletePersonalTime | `block`, `reblock`, `unblock`, walk blocks        |

the MCP server is driven two ways: the repo's skill
(`skills/awsevents-muse/SKILL.md`) encodes the call rules both
interfaces follow, and the per-assistant guides give the exact
config for kiro-cli (loopback OAuth that works), Meta Muse, Copilot,
and Gemini (all verified live, limits documented).

## setup, dependencies, how to run

dependency: python 3.10+, nothing to install (standard library only).

```
git clone git@github.com:chasko-labs/reinvent26-attendee-planner.git reinvent26-planner
cd reinvent26-planner/cli
python3 -m reinvent26 status reinvent2026   # sign-in state, no secrets printed
python3 -m reinvent26 login                 # Builder ID, loopback callback
python3 -m reinvent26 sessions reinvent2026 # cache the catalog
python3 -m reinvent26 fill --dry-run        # preview the week
```

no sign-in handy: `python3 -m reinvent26 events` and
`python3 demo/demo_public.py` both work without one. full runbook:
`docs/sign-in.md`. nightly automation: `docs/daily-new-sessions.md`.

## demo to record

1. `status` → signed in, schedule readable with counts.
2. `fill --dry-run` → scarcity-ordered plan with per-pick reasons.
3. `find-me --day 1` → shareable meetup page for the site.
4. watcher report → new sessions, launch signals, kiro-cli handoff.
5. assistant reads the report in Meta Muse and answers "where is
   bryan free for lunch Thursday" (no connector needed).
