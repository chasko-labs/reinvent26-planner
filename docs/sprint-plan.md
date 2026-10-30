# sprint plan: fill the week (2026-10-30 to re:invent)

planned 2026-10-30 by a five-role subagent team (product, tech lead,
rebalance, coverage, qa) plus a completeness critic and a synthesis pass.
no human reviewed the queue; rulings below are the operator's, encoded so
both booking commands agree.

## sprint goal

protect the 13 held mon-fri seats and convert the first released fitting
seat into a 14th seat via a single by-hand booking before re:invent
(nov 30-dec 4, 2026). logistics first, no unattended booking.

baseline: main @8d49fc6, 108 pytest green, 100 fitting sessions
live-checked unavailable, 46-48 conference-wide open seats all
clash/repeat/excluded — 13 is the no-cancel ceiling (and every remaining
open seat is a swap candidate, not an add).

## p0 — do first

- P0.1 token-write resilience. owner: tech lead. effort: m.
  accept when `fill --dry-run` exits 0 without a mid-run sso expiry. if no
  non-sso roles-anywhere ssm writer exists, the sprint formally accepts
  hand-run-after-sso-login (sso 8h expiry; in-memory fallback on write
  failure). no live booking until this passes.
- P0.2 refresh catalog + seats sweep to one fresh vintage. owner:
  operator + tech lead. effort: s (~10 min, 1484 getSession calls via the
  .cache sweep_chunk pattern; seats.py alone writes seats.json and does
  not satisfy rebalance). accept when seats-sweep.json holds >=1000
  entries (target 1484) with 0 dropped errors and the open count is
  reconciled (46 vs 48 dispute closed on one snapshot).
- P0.3 manual fill cadence, never looped. owner: operator. effort: s per
  run (~15 s). escalating: weekly from oct 30, daily the final week,
  twice-daily by hand nov 30-dec 4. each run is one `fill` pass — fill
  never cancels, so dry-run-first is reserved for rebalance. transcript +
  getSchedule count reviewed each run.
- P0.4 rebalance only via dry-run transcript + approval, then one live
  run. owner: operator + qa. effort: m. today's shape: 13 seats/1260 min
  -> 15/1260 min (aim433 + stg338-r over aim318; ind322-r + ind3304-r1
  over sec318-r1 — read as 2 cancels, not the double-printed 4). live run
  only after the dry-run transcript is approved; verify by getSchedule.
  qa enforces the transcript review: dry-run-first is process-only in
  code (live rebalance cancels first immediately).
- P0.5 decide the wed 14:30-15:30 gap-killed window (24 sessions). owner:
  product/operator. effort: s analysis. either one bookable seat unlocks
  by venue/swap analysis (forum inv537 -> mgm aim434, 60-min mgm gap both
  directions) or the window is recorded as dead. rebalance-only territory.
- P0.6 lock the single booking objective (rulings applied, no human
  asked):
  - tue morning: format wins — tnc315-r lab (90 m) over tnc306-r exam prep
    (180 m). hands-on format outranks minutes under the standing ranking.
    p1.2 aligns plan_days so fill and rebalance pick the same winner.
  - friday: workshop wins alone — svs401-r1 (prio 36.0, best bookable
    session all week) over two chalks. format over count accepted.
  - excluded-only windows stay empty: bedrock/frontier exclusions are the
    operator's own config, harder than 'any session beats no session'.
    reversible by editing map-config.json. fill and rebalance already
    agree here; the ruling is recorded, no code change.

## p1 — next

- P1.1 ranked walk-up queues per open window. owner: product. effort: m.
  wed-am rank 1 (45 fits, 2-seat ceiling; chain-critical slots api310
  12:00 forum, net405-r1 10:00 mgm, ant438-r1/stg332-r1 11:30 mgm),
  fri rank 2 (svs401-r1 watch; fri 12:30-18:00 dead for reserved seats —
  no reservable catalog after 12:30), tue-am rank 3 (2 candidates, 1 seat).
- P1.2 rebalance safe in code. owner: tech lead. effort: m. live
  rebalance refuses without a prior dry-run record; catalog/sweep age
  checked (not only >=1000) before any cancel-first swap; prompt the
  'replacing X' double-print so approvals read true cancel counts.
  document that --dry-run still networks and overwrites schedule.json.
- P1.3 close test gaps. owner: qa + tech lead. effort: m. offline mock
  tests for cancel-first + rebook (rebook result currently discarded,
  cancel loop has no try/except) and personal-time awareness (fill
  ignores schedule.personalTime today and can book over lunch/travel
  blocks). 108 tests stay green.
- P1.4 hygiene + deadline split. owner: tech lead. effort: s. delete the
  3 merged local branches (ancestors of main, safe); prune stale
  origin/issue-* only after github pr state confirms squash-merge; decide
  .kiro/mcp.json + overlay intent (commit or gitignore). split the two
  deadlines: hackathon submission 2026-11-06 23:59 pt (article/readme)
  tracked separately from nov 30 seat work; fix stale 409 text
  ('opens 8 oct 2026') in api.py and hackathon-alignment.md.

## p2 — opportunistic

- P2.1 full-but-interesting value: 244 no-seat sessions (72 youtube-flagged)
  become a post-event watch list; 354 presenters a follow list.
- P2.2 refactor guard in .githooks/pre-commit: fail when public fill.py
  surface (fits, priority, window, ssm_token) disappears.
- P2.3 after any accepted swap: `reinvent26 map`, review docs diff,
  refresh the live-state numbers in docs/mcp-approach.md from the new
  getSchedule snapshot.

## explicitly not now

- no background/looped booking in any form. the systemd/cron recipe in
  docs/daily-fill.md stays reference-only for other attendees and must not
  be installed on this host; the overnight 18-pass loop (0/1700 opened)
  must not be resurrected; no scheduler in fill.
- no unattended runs before a non-sso writer exists. no live rebalance
  without a dry-run transcript + approval. no fill watches for fri pm or
  wed 14:30-15:30. no new l-scope builds (scheduler, token-taking ranker,
  repo ci) — every item above is s or m.

## top risks

- cancel-first loss window: cancel succeeds, book fails, rebook fails
  silently (result discarded in code); a seat taken in between is gone.
  mitigated by dry-run + live recheck, not eliminated.
- stale mixed-vintage snapshots (catalog oct 29, sweep oct 30 01:33,
  schedule 15:40) authorising swaps with no freshness gate.
- token rotation/loss mid-run; sso 8h expiry; event-week re-login owner
  unassigned.
- sweep cost: 1484 getSession calls, up to ~4452 with retries, no 429
  breaker (fill's 30 s/400-check guard does not cover the sweep).
- release probability unknown (only sample: 0 releases in 18 overnight
  passes, 32 days out) — cadence yield cannot be sized.

## first-day checklist

1. confirm main @8d49fc6, `pytest -q` = 108 passed.
2. sso login via ssh tunnel (port 8484) if needed; `fill --dry-run`
   exits 0.
3. record cache timestamps/counts (catalog, seats-sweep >=1000,
   schedule = 13 reserved).
4. list event-week personal-time blocks (pace for p1.3).
5. run the fresh sweep; reconcile the open count (p0.2).
6. review the rebalance dry-run transcript (2 cancels, not 4); hold for
   approval — do not run live.
7. put the cadence on a calendar; name the event-week runner and login
   owner. no cron/systemd.
8. decide .kiro intent; confirm the nov 6 hackathon track is tracked
   separately.

## effort key

s < 0.5 day, m 1-3 days, l > 3 days. no l items — remaining work is
operational, not build.
