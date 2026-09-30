# session data schema and ingest layout

how session data enters and lives in this repo. the Events API stays the
source of truth for a signed-in attendee's real schedule; everything under
`data/` is a curated, offline, human-fed catalog that the planner can rank,
clash-check, and slot without a token or a network call.

## format decision: json arrays of session objects

one array of session objects per file, utf-8, two-space indent, trailing
newline. json over yaml/csv because:

- `schedule.normalize_session` / `match_topics` / `rank.compact_session`
  already consume python dicts with exactly these keys. json loads straight
  into that shape with the stdlib, no parser dependency (the repo is
  stdlib-only outside the optional rust filter).
- the live API returns json in the same family of shapes; a curated file
  and a cached `.cache/<eventId>/sessions.json` stay interchangeable.
- arrays keep provenance simple: one file per source paste / topic block,
  named for where it came from, so re-feeding is append-a-file not
  merge-a-blob.

## canonical session object

the ranker (`schedule._text_fields`) reads `title, code, abbreviation,
tracks, topics, services, level, sessionType`. the clash/slot logic reads
`startTime, endTime`. `normalize_session` fills canonical fields from live
shapes, so a curated file may use either the canonical keys or the live
keys and still work. curated files here use the canonical keys.

| field         | type        | required | notes                                                        |
| ------------- | ----------- | -------- | ------------------------------------------------------------ |
| `sessionId`   | string      | yes      | stable unique id; lowercased code plus a suffix (`arc322-a`) |
| `code`        | string      | yes      | catalog code as printed (`ARC322`, `IND367-R1`)              |
| `title`       | string      | yes      | session title, verbatim                                      |
| `level`       | string      | yes      | `"100"`..`"500"` (foundational..distinguished)               |
| `sessionType` | string      | no       | breakout, chalk talk, workshop, builders, lightning, code, gameday, bootcamp |
| `topics`      | string[]    | yes      | curated keyword tags the ranker matches on (see tagging)     |
| `services`    | string[]    | no       | full AWS service names, never abbreviated                    |
| `tracks`      | string[]    | no       | catalog track / area of interest, verbatim                   |
| `lenses`      | string[]    | no       | interest-category tags from the controlled lens vocabulary   |
| `startTime`   | string|null | no       | ISO local `YYYY-MM-DDTHH:MM:SS`, no `Z`; null when timeless  |
| `endTime`     | string|null | no       | ISO local; null when timeless                                |
| `room`        | string      | no       | venue plus room where known (`MGM Grand`)                    |
| `venue`       | string      | no       | venue only, when room detail is absent                       |
| `sponsored`   | boolean     | no       | true for `-S` partner sessions                               |
| `abstract`    | string      | no       | full abstract; ranker/model reads first 300 chars            |
| `source`      | string      | no       | provenance tag: where this row was fed from                  |

timeless rows (no confirmed slot) set `startTime`/`endTime` to null. filters
keep them; clash and slot logic skip them. this matches how
`filter_by_time` and `find_open_slots` already treat missing timestamps.

## time handling

pasted PST wall-clock times are written as local ISO with no zone and no
`Z`, matching `demo/sessions-sample.json` and what `schedule._parse`
expects. re:Invent 2026 runs Mon Nov 30 through Fri Dec 4. day mapping used
across curated files:

- Monday, Nov 30   -> 2026-11-30
- Tuesday, Dec 1   -> 2026-12-01
- Wednesday, Dec 2 -> 2026-12-02
- Thursday, Dec 3  -> 2026-12-03
- Friday, Dec 4    -> 2026-12-04

a lightning talk with a start and no printed end gets a 20-minute end; a
session with a start and no end gets a 60-minute end; a row with no time at
all stays timeless (null/null).

## file layout under data/

```
data/
  reinvent2026/
    aerospace-leo.json        # Amazon Leo / satellite / HPC block
    intelligence.json         # "intelligence" + location-intelligence block
    <next-paste>.json         # one file per feed, named for its source
    index.json                # optional manifest: file -> count, source, fed date
```

`source` on each row and the file name both carry provenance so a re-feed
is idempotent-ish: same source paste overwrites its own file, never a
silent merge into a shared blob.

## tagging convention (topics)

`topics` is the lever the bare `shortlist` and `match_topics` rank on. tags
are lowercase, hyphenated, and drawn from a controlled-ish vocabulary so a
`--topics agents,mcp` query lands. baseline vocabulary in play:

`agents, agentic, mcp, bedrock, agentcore, generative-ai, knowledge-graph,
rag, vector, sagemaker, textract, rekognition, computer-vision, location,
geospatial, edge, cloudfront, serverless, lambda, observability, security,
fraud, cost-optimization, migration, modernization, kiro, physical-ai,
world-models, iot, satellite, connectivity, hpc, database, aurora, neptune`

industry lens tags live in `industries`, not `topics`, so a topic query and
a domain query stay separable.

## lens vocabulary (interest-tracking categories)

`lenses` is a fixed, small controlled vocabulary — the interest categories
being tracked across the catalog. it is separate from `topics` (technical
keywords) and `tracks` (verbatim catalog tracks) so an interest query and a
technology query stay independent. a session may carry more than one lens.

| lens             | covers                                                                 |
| ---------------- | ---------------------------------------------------------------------- |
| `favorites`      | bryan's personal favorites, hand-picked regardless of other lens        |
| `ai`             | core AI/ML: models, inference, agents, kernels, neurosymbolic, voice     |
| `self-managed-agents` | run your own models/agents/MCP on infra you control: VM isolation, self-hosted inference, open weights, sovereignty, hybrid edge |
| `real-estate`    | property, listings, valuation, rental, proptech, the realtor.com lens  |
| `space-satellite`| Amazon Leo, low-earth-orbit connectivity, aerospace, HPC for space      |
| `next-gen-stats` | analytics, business/operational intelligence, telemetry, location data  |
| `video-games`    | gameday, gamified learning, world models and physical-AI for simulation |
| `nvidia`         | NVIDIA-sponsored or NVIDIA-relevant: cuVS, GPU accel, GR00T/Cosmos, etc |

a session lands in a lens when the abstract or services clearly serve that
interest, not on a single incidental keyword. the tagging is editorial and
lives in the curated `data/` files, reviewed like any other content.

## watchlist entries

`data/reinvent2026/watchlist.json` holds tracked-but-unfilled gaps: topics
worth a session that has not been found in the catalog yet. these rows use
`sessionType: watchlist`, `source: watchlist-gap`, `level: "0"`, and null
start/end times so they surface under their lens but are skipped by clash
and slot logic (timeless). the abstract states what to look for and the
search leads. when a real session surfaces, the watch row is replaced with
the real code/title/time and moved into the matching lens file. this keeps
gaps as visible catalog items instead of prose that has to be re-flagged.

## how curated data reaches the planner

the loader resolves a catalog for an event id by, in order: an explicit
`--data <path>` file, then the curated `data/reinvent2026/*.json` merged by
`sessionId` (later files win on collision), then the on-disk
`.cache/<eventId>/sessions.json`, then a live fetch. curated data is
offline and tokenless, same class as the demo samples. the wiring that
merges `data/` into the catalog path is CLI code (owned by a coder ghost);
this doc is the contract that wiring targets.
