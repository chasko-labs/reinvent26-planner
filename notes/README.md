# notes: stream-of-consciousness inbox

repo-local scratch surface for raw thinking about re:Invent 2026 planning.
drop thoughts here as you have them. this is the feed that shapes the
shortlist without touching `~/writing`.

## how it flows into the planner

the `shortlist` command ranks on topic seeds. today seeds derive from
`~/writing` via `seeds.py`. this `notes/` directory is the repo-local
equivalent: your re:Invent-specific thinking lives here, close to the
sessions it is about, versioned with the plan.

two paths, both stdlib, both offline:

- seeds: the ingest wiring points seed derivation at `notes/` (or merges
  `notes/` with `~/writing`) so a bare `shortlist` reflects what you have
  been writing about re:Invent, not just the ComfyUI/SDXL beats currently
  in `seeds.json`
- rank: any single note can be fed straight to the local-model ranker as a
  `--query`, e.g. the model reads a note and ranks the cached catalog
  against it

## format: one markdown file per thread

- `notes/<slug>.md` — one file per line of thinking (e.g.
  `notes/real-estate-angle.md`, `notes/leo-edge-resilience.md`)
- freeform. headings, bullets, half-sentences all fine. the seed deriver
  strips code fences, inline code, and urls, then counts unigrams, so
  prose is what shapes seeds
- put a session code in a note (`AIM247-S`) and it stays greppable against
  the curated catalog under `data/reinvent2026/`

## relationship to the other surfaces

| surface                    | what it holds                        | who owns it        |
| -------------------------- | ------------------------------------ | ------------------ |
| `notes/`                   | raw stream-of-consciousness thinking | you, freeform      |
| `data/reinvent2026/*.json` | curated catalog, one file per feed   | editorial, schema  |
| `docs/*-lens.md`           | the POV built from notes + research  | product owner      |
| `cli/reinvent26/seeds.json`| derived topic seeds                  | generated          |

notes are the input, the lens docs are the output, the curated data is the
catalog they reason over.
