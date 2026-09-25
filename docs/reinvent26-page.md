# draft copy for bryanchasko.com/reinvent26

> Handoff note for issue #13: the published TypeScript page ships in the
> bryan-chasko-com repo (as `content/reinvent26`), not here. Copy the body
> below there, preserving the frontmatter. This file stays as the draft
> source. On publish, replace the article placeholder with the builder.aws.com
> URL and link the live page back from the planner README.

```yaml
# suggested frontmatter for content/reinvent26 in bryan-chasko-com
title: "Plan re:Invent 2026 with an agent"
slug: reinvent26
description: "Catalog search, clash check, and open slots for re:Invent 2026."
repo: https://github.com/chasko-labs/reinvent26-planner
article: TODO-builder-aws-post-url # issue #12, publish before 6 Nov 2026
```

## headline

Plan re:Invent 2026 with an agent: catalog search, clash check, open slots.

## what this project does

- pulls the full re:Invent 2026 session catalog through the Events API
- shortlists 300/400 level sessions by topic (agents, mcp, serverless, data)
- maps your live AWS footprint to catalog topics (stack-aware pick) instead
  of relying on memory
- finds sessions that fit your free windows (open slot finder)
- checks your schedule for double bookings
- favorites now, reserves after 8 Oct 2026, confirms every write with GetSchedule
- try it with no token: `python demo/demo_public.py` (cached samples;
  full transcript in `demo/sample-output.txt`)

## how to use it

1. list events, pick the re:Invent 2026 event id
2. run shortlist with your topics, pull abstracts for the shortlist only
3. favorite now; reserve after seating opens; re-check schedule
4. full setup and commands: repo README

Live commands (need `EVENTS_ACCESS_TOKEN` plus event registration):

```
cd cli
python -m reinvent26 events
python -m reinvent26 shortlist <eventId> --topics agents,mcp,bedrock --level 3 --top 20
python -m reinvent26 schedule <eventId>
```

## key dates

- favorites: work now
- reserved seating on site: 6 Oct 2026
- reserve/cancel through the API: 8 Oct 2026 (409 before then)
- submission deadline: 6 Nov 2026 11:59 pm PT

## links

- repo: https://github.com/chasko-labs/reinvent26-planner
- article: TODO-builder-aws-post-url (Builder Center post, issue #12)
- Events API overview: https://docs.aws.amazon.com/events/latest/devguide/what-is-events-api.html
- hackathon: builder.aws.com hackathons page (re:Invent event catalog API hackathon)

## handoff checklist

- [ ] body copied to `content/reinvent26` in bryan-chasko-com
- [ ] repo link present on the live page
- [ ] article link present on the live page once #12 publishes
- [ ] live page URL linked back from planner README and this draft
