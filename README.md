# reinvent26-planner

Entry for the reinvent event catalog api hackathon (24 sep - 6 nov 2026).
Helps attendees plan reinvent 2026: shortlist sessions, map their live
Amazon Web Services footprint to catalog topics, find open slots, check
double bookings, favorite now, reserve after seating opens.

## what it is

Three ideas in one small repo:

1. conflict solver: full catalog pull, 300/400 shortlist, clash check,
   favorites plus personal time, GetSchedule confirm.
2. stack-aware picker: maps live resource types (Lambda, DynamoDB,
   Bedrock, ...) to catalog keywords so the shortlist reflects what you
   actually run.
3. open slot finder: given free windows, returns sessions that fit with no
   clash.

Plus a Muse Code skill (`skills/awsevents-muse/SKILL.md`) and an optional
rust pre-filter (`rust/catalog-filter`) for large cached catalogs.

## how it uses the API

- REST (`cli/`): ListEvents (public), ListSessions with pagination until
  `nextToken` is absent, GetSession, GetSchedule, favorites and
  reservations in batches of 1-10, personal time create.
- first pass uses `includeAbstracts=false`, then pulls abstracts for the
  shortlist only.
- every batch write is followed by GetSchedule confirm; http 200 does not
  imply every session succeeded.
- reserve/cancel returns 409 until 8 Oct 2026; favorites and reads work now.
- MCP path: the skill documents the awsevents server
  (`https://api.awsevents.com/mcp`, PKCE, public client id) for interactive
  agent sessions. The cli is the scriptable surface.

## setup

needs: python 3.11+, rust toolchain only for the optional filter.

```
cd cli
python -m reinvent26 events
export EVENTS_ACCESS_TOKEN=<builder-id-access-token>
python -m reinvent26 sessions <eventId> | head
```

## run

```
# shortlist 300/400 level agent sessions
python -m reinvent26 shortlist <eventId> --topics agents,mcp,bedrock --level 3 --top 20

# schedule plus double bookings
python -m reinvent26 schedule <eventId>

# sessions fitting free windows (room plus venue shown for back-to-back)
python -m reinvent26 slots <eventId> \
  --window 2026-12-01T13:00:00,2026-12-01T16:00:00 \
  --window 2026-12-02T09:00:00,2026-12-02T12:00:00

# stack-aware pick: keywords from live resources, then shortlist
python -m reinvent26 stack-pick <eventId> --profile my-readonly-profile --top 10
python -m reinvent26 stack-pick <eventId> --resources-json /tmp/resources.json

# shortlist with preferences: daytime bounds, lunch block, one outsider pick
python -m reinvent26 shortlist <eventId> --topics agents,mcp \
  --not-before 09:00 --not-after 17:00 --lunch 12:00-13:00
python -m reinvent26 shortlist <eventId> --topics agents --offbeat

# bare shortlist uses blog-aware seed topics (cli/reinvent26/seeds.json);
# --reseed regenerates them from ~/writing, --topics always overrides
python -m reinvent26 shortlist <eventId>
python -m reinvent26 shortlist <eventId> --reseed

# favorite (works now, 10 per call)
python -m reinvent26 favorite <eventId> <id1,id2>

# reserve (api opens 8 Oct 2026; 409 before then)
python -m reinvent26 reserve <eventId> <id1,id2>
```

## catalog cache plus rust pre-filter

`shortlist` and `sessions` save the fetched catalog to
`.cache/<eventId>/sessions.json` (gitignored). Repeat with `--cached` for no
network; `--refresh` refetches and overwrites. With `--cached`, shortlist
pipes through the rust helper when built, else python filters directly:

```
cargo build --release --manifest-path rust/catalog-filter/Cargo.toml
python -m reinvent26 shortlist <eventId> --topics agents --cached
python -m reinvent26 shortlist <eventId> --topics agents --cached --day 2026-12-01
```

## tests

```
python -m pytest -q
cargo test -p catalog-filter --manifest-path rust/catalog-filter/Cargo.toml
```

## key dates

favorites now; reserved seating on site 6 Oct 2026; full write access
through the API 8 Oct 2026; submissions close 6 Nov 2026 11:59 pm pt.

## eligibility note

contest is open to current Heroes and Community Builders registered to
attend reinvent 2026. Confirm registration on the reinvent site before
expecting catalog access; a valid token without registration returns 403.

## docs

- skill: `skills/awsevents-muse/SKILL.md`
- local models and caching: `docs/local-models.md`
- draft copy for bryanchasko.com/reinvent26: `docs/reinvent26-page.md`
- canonical Events API docs: https://docs.aws.amazon.com/events/latest/devguide/what-is-events-api.html
