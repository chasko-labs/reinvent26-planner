# Builder Center article draft: plan re:Invent 2026 with an agent (DRAFT, unpublished)

Status: draft for issue #12. Publish to builder.aws.com before 6 Nov 2026,
then replace the placeholder links in README.md and docs/reinvent26-page.md
with the published URL. Do not paste access tokens into the article.

## working title

Plan re:Invent 2026 with a scriptable agent: shortlist, clash check, open slots

## what was built

reinvent26-planner (`https://github.com/chasko-labs/reinvent26-planner`) is a
small stdlib-only planner for re:Invent 2026:

1. conflict solver: full catalog pull, 300/400 shortlist, clash check,
   favorites plus personal time, GetSchedule confirm.
2. stack-aware picker: maps live resource types (Lambda, DynamoDB, Bedrock,
   ...) to catalog keywords so the shortlist reflects what you actually run.
3. open slot finder: given free windows, returns sessions that fit with no clash.

Plus a Muse Code skill (`skills/awsevents-muse/SKILL.md`) and an optional
Rust pre-filter (`rust/catalog-filter`) for large cached catalogs.

## why

The catalog is large and session times shift as rooms settle. Shortlisting by
topic alone misses what attendees actually run, and double bookings are easy
to miss across days. The planner keeps one source of truth (GetSchedule),
ranks by topics plus live footprint, and surfaces clashes before favorites
become reservations.

## how it uses the REST surface

- `ListEvents` (public, no token) to find the re:Invent 2026 event id.
- `ListSessions` with pagination until `nextToken` is absent; first pass uses
  `includeAbstracts=false`, then `GetSession` pulls abstracts for the
  shortlist only.
- Favorites and reservations in batches of 1-10; every batch write is
  followed by a `GetSchedule` confirm because HTTP 200 does not imply every
  session succeeded.
- `reserve`/`cancel` returns 409 until 8 Oct 2026; favorites and reads work now.
- MCP path: the skill documents the awsevents MCP server
  (`https://api.awsevents.com/mcp`, PKCE) for interactive agent sessions.
  The Python CLI is the scriptable surface. See `skills/awsevents-muse/SKILL.md`.
- Token hygiene: `EVENTS_ACCESS_TOKEN` via env only, never logged, never in
  URLs or reports. Tokens last 60 minutes.

## demo transcript (no token required)

One-command public demo using cached samples:

```
python demo/demo_public.py
```

Full output is checked in at `demo/sample-output.txt`. Excerpt:

```
## shortlist: topics=agents,mcp,bedrock level=300/400 top=3
CON401 | MCP servers in production: auth and tool design | 400 | 2026-12-01T09:30:00->2026-12-01T10:30:00 | Venetian L3
ANT301 | Agent orchestration with Bedrock Agents | 300 | 2026-12-01T09:00:00->2026-12-01T10:00:00 | Venetian L2
DAT402 | Data modeling with DynamoDB for agent memory | 400 | 2026-12-01T13:00:00->2026-12-01T14:00:00 | Venetian L2

## schedule with clash check
ANT301 | Agent orchestration with Bedrock Agents | 300 | 2026-12-01T09:00:00->2026-12-01T10:00:00 | Venetian L2
CON401 | MCP servers in production: auth and tool design | 400 | 2026-12-01T09:30:00->2026-12-01T10:30:00 | Venetian L3
SRV301 | Event-driven serverless with Lambda and EventBridge | 300 | 2026-12-01T11:00:00->2026-12-01T12:00:00 | MGM Grand
# clash: ANT301 x CON401
```

Screenshots to add at publish time: (1) shortlist output, (2) clash line,
(3) `favorite` plus `schedule` (GetSchedule) confirm on a registered event.
The authenticated step is intentionally not in the token-free demo; run:

```
export EVENTS_ACCESS_TOKEN=<builder-id-access-token>
python -m reinvent26 favorite <eventId> <id1,id2>
python -m reinvent26 schedule <eventId>   # GetSchedule confirm
```

## key dates

- favorites: work now
- reserved seating on site: 6 Oct 2026
- reserve/cancel through the API: 8 Oct 2026 (409 before then)
- submission deadline: 6 Nov 2026 11:59 pm PT

## publish checklist

- [ ] post published on builder.aws.com
- [ ] repo link in post
- [ ] README.md "article" link replaced with published URL
- [ ] docs/reinvent26-page.md "article" link replaced with published URL
- [ ] screenshots or transcript attached (shortlist, clash, favorite + GetSchedule)
