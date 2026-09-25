# local models and caching (optional)

The planner works with plain REST and needs no local model. This page covers
optional acceleration when the catalog grows large.

## when to use what

- default: python cli paginates the live API directly. No cache, no model.
- large first pass: pipe a cached session list through
  `rust/catalog-filter` for sub-second keyword/level/day filtering.
- natural language shortlist: point any OpenAI-compatible local endpoint
  (e.g. `http://127.0.0.1:8181/v1`) at cached catalog json and ask for a
  ranked shortlist. Keep the API as source of truth; the model only ranks.
- cache: store fetched pages under `.cache/<eventId>/sessions.json` and
  re-filter locally instead of re-fetching. Refresh per day; catalog data
  changes as rooms and times settle.

## rust helper build

```
cargo build --release -p catalog-filter
sessions.json -> ./target/release/catalog-filter --topics agents,mcp --levels 300,400
```

## rank command

```
python -m reinvent26 rank --cache .cache/<eventId>/sessions.json \
  --query "agents for a python dev, nothing before 9am" \
  --endpoint http://127.0.0.1:8181/v1 --model local --top 10
```

Time floors: `--not-before HH:MM` wins when given; otherwise the query is
scanned for "nothing before 9am" / "after 9am" style phrases and earlier
sessions are dropped before the model sees them.

## PROMPT (mirrored by `rank.build_prompt`)

```
system: You rank reinvent session catalogs. Reply with JSON only:
{"picks": [{"code": "<SESSION CODE>", "reason": "<one line>"}]}.
Rank at most <top> sessions, best first.
Use only codes from the catalog below; never invent codes.

user:
request: <natural-language query>

catalog (code | title | level | start | topics):
<CODE> | <title> | <level> | <startTime> | <topics>
... (one line per eligible cached session)
```

The cli validates every returned code against the cached catalog (the
source of truth), drops unknown codes, dedupes, and prints `summarize`
lines. Unknown-code-only replies exit non-zero (`model returned no
catalog codes`).

## notes

- never send access tokens to a local model process you do not control.
- public catalog json is safe to rank locally; schedule writes always go
  through the authenticated API path plus GetSchedule confirm.
