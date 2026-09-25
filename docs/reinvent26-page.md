# draft copy for bryanchasko.com/reinvent26

Lives here as a draft. The published typescript page belongs in the
bryan-chasko-com repo (content/reinvent26) and is a separate change.

## headline

plan reinvent 2026 with an agent: catalog search, clash check, open slots.

## what this project does

- pulls the full reinvent 2026 session catalog through the Events API
- shortlists 300/400 level sessions by topic (agents, mcp, serverless, data)
- maps your live Amazon Web Services footprint to catalog topics
  (stack-aware pick) instead of relying on memory
- finds sessions that fit your free windows (open slot finder)
- checks your schedule for double bookings
- favorites now, reserves after 8 Oct 2026, confirms every write with
  GetSchedule

## how to use it

1. list events, pick the reinvent 2026 event id
2. run shortlist with your topics, pull abstracts for the shortlist only
3. favorite now; reserve after seating opens; re-check schedule
4. full setup and commands: repo README

## key dates

- favorites: work now
- reserved seating on site: 6 Oct 2026
- reserve/cancel through the API: 8 Oct 2026 (409 before then)
- submission deadline: 6 Nov 2026

## links

- repo: https://github.com/chasko-labs/reinvent26-planner
- Events API overview: https://docs.aws.amazon.com/events/latest/devguide/what-is-events-api.html
- hackathon: builder.aws.com hackathons page (reinvent event catalog api hackathon)
