# hackathon alignment: re:Invent Event Catalog API Hackathon

living checklist tying the work in this repo to the contest rules and judging criteria. update as items land

## dates

| milestone | date | status |
| --- | --- | --- |
| api and mcp server live | 2026-09-21 | done |
| hackathon announced | 2026-09-24 | done |
| reserved seating opens | 2026-10-06 | passed; verify live |
| full write access (reserve/cancel) | 2026-10-08 | passed; verify live |
| submission deadline | 2026-11-06 23:59 pt | 8 days from 2026-10-29 |
| winners selected | by 2026-11-27 | pending |
| top 3 featured at re:invent | 2026-11-29 to 2026-12-04 | pending |

## correction

earlier notes in this repo say reserve/cancel returns 409 until 8 oct 2026 (README.md, docs/article-draft.md, skills/awsevents-muse/SKILL.md). today is 2026-10-29, so that gate has passed. those lines are stale and the 409 behavior needs a live re-test. until tested, treat reserve/cancel as unverified

## submission requirements

| requirement | state | owner |
| --- | --- | --- |
| public code repo with working code | repo is public (chasko-labs/reinvent26-planner) | done |
| readme: setup, dependencies, how to run | exists; needs refresh for mcp path, event map, ledger, stale 409 text | open |
| published article on builder.aws.com | docs/article-draft.md is a draft only | open |
| article explains what, why, and how it uses api or mcp | draft covers cli; mcp path and event map still to add | open |
| original work | yes | done |
| eligibility: current aws hero or community builder, registered for re:invent, 18+ | confirmed by bryan: aws hero, registered. protected catalog reads succeeded with his token, which the api only allows for registered attendees | done |

## judging criteria and evidence

| criterion (25% each) | evidence we have or need |
| --- | --- |
| creativity and novelty | ssh-tunneled pkce login for a headless host; ssm-held tokens; logistics-aware scheduler (venue gaps, anchors, topic weights); launch ledger; "not conducive to logistics" interest board for teammates |
| utility for attendees | docs/event-map.md plus the cli: shortlist, slot finder, schedule, personal time blocks. need: clean demo of wall-to-wall reserved-seat planning |
| technical depth and api surface | uses: list events, paginated sessions with abstracts, favorites, schedule, personal time. need: reserve and cancel once re-verified, and the mcp server end to end (tools/list, tool calls) |
| builder center article quality | draft exists. need: screenshots or sample output, architecture diagram, honest lessons section from docs/hackathon-awsevents-mcp-log.md |

## api surface coverage

| capability | cli | mcp | verified |
| --- | --- | --- | --- |
| list events | yes | pending | live, 2026-10-29 |
| list sessions (paginated, abstracts) | yes | pending | live, 2350 sessions |
| favorites | yes | pending | not run today |
| view schedule | yes | pending | not run today |
| personal time blocks | yes | pending | not run today |
| reserve / cancel | yes | pending | not run; retest |

## open work, in order

- re-test reserve and cancel against the live api; fix stale 409 text everywhere
- finish the mcp bridge, run tools/list and one real tool call, record the tool names
- done: event map generator lives in cli/reinvent26/mapper.py (`python -m reinvent26 map`), config in data/reinvent2026/map-config.json, catalog snapshot persisted at .cache/reinvent2026/catalog.json
- favorite the scheduled sessions through the api, then reserve when verified
- refresh readme, record a short demo, draft the builder center article from the hackathon log
- publish the article and submit before 2026-11-06 23:59 pt, aiming for 2026-11-04 to leave margin

## story for the article

the build log is the narrative. device code login was not available, so a tunnel carries the pkce callback to a browser on another machine. tokens live in aws systems manager parameter store. the catalog feeds a scheduler that treats venue travel time as a constraint, which is the part generic session browsers skip. raw material: docs/hackathon-awsevents-mcp-log.md
