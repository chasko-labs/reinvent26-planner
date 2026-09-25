---
name: awsevents-muse
description: Work with the Amazon Web Services Events API (api.awsevents.com) from Muse Code to discover reinvent and summit session catalogs and manage the signed-in attendee schedule (reservations, favorites, personal time). Use when a request mentions the Events API, reinvent session catalogs, favorites, reservations, or personal event schedules.
---

# Events API for Muse Code

Acts only for the signed-in attendee. Reads catalogs, alters that attendee's
own schedule. Cannot register anyone for an event or read another schedule.

## Canonical sources (read before behavior questions)

- overview: https://docs.aws.amazon.com/events/latest/devguide/what-is-events-api.html
- getting started: https://docs.aws.amazon.com/events/latest/devguide/getting-started.html
- mcp server: https://docs.aws.amazon.com/events/latest/devguide/mcp-server.html
- auth: https://docs.aws.amazon.com/events/latest/devguide/authentication.html
- rest: https://docs.aws.amazon.com/events/latest/devguide/rest-api.html
- openapi: https://api.awsevents.com/v1/openapi.json
- errors/quotas: https://docs.aws.amazon.com/events/latest/devguide/errors.html and .../quotas.html

No Amazon Web Services documentation is bundled here. Check the live pages
when dates, quotas, or error behavior matter.

## Interface choice

- agent work in this repo: use the python cli in `cli/` (REST). Public
  `ListEvents` needs no sign-in; protected catalog reads plus all schedule
  writes need a Bearer access token and event registration.
- interactive agent sessions may use the awsevents MCP server at
  `https://api.awsevents.com/mcp` (streamable http, PKCE, public client id
  `7vmom55m1qstvq8i71ph127bfq`). Every MCP tool call requires sign-in,
  including `ListEvents`.

## Rules that are easy to get wrong

- paginate `ListSessions` until `nextToken` is absent. A short page is not
  the last page.
- first catalog pass: `includeAbstracts=false`, then fetch abstracts for the
  shortlist only.
- writes go 1-10 session ids per call. Favorites record interest; they do
  not reserve seats.
- http 200 on a batch does not mean every session succeeded. Inspect each
  per-session result, then confirm with `GetSchedule` before reporting.
- reserve/cancel through the API returns 409 until 8 Oct 2026. Reading plus
  favoriting work now. 409 means retry after reopen, not a bad request.
- 403 with json body: valid token but not registered for the event. Signing
  in again does not fix it; register on the reinvent site first.
- 404 on cancel/remove means already absent; treat as complete on retry.
- after an unknown write outcome (timeout, 500, 503): do not repeat blindly.
  Read `GetSchedule`, compare with intent, submit only what remains.
- access tokens last 60 minutes, refresh tokens 30 days. Never log tokens or
  put them in urls, reports, or chat output.
- confirm event id plus exact sessions before any schedule change unless the
  user already stated them unambiguously.

## Repo workflow

- `python -m reinvent26 events` then `sessions <eventId>` (see `cli/` README
  path in root README).
- shortlist: rank by topic keywords, filter level 300/400, pull abstracts
  for the shortlist only.
- stack-aware pick: map live resource types via `stack_keywords`, then
  shortlist with those keywords.
- open slots: pass free windows to `find_open_slots` to skip clashes.
- report event id, interface used, per-session failures, and whether
  `GetSchedule` confirmed each write.
