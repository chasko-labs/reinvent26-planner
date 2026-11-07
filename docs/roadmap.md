# roadmap: planned planner work

ordered by value over effort. each item states what ships and why it
matters for bryan's week. nothing here needs another service until
item 10.

## now (cli-sized)

1. scarcity-first booking with reasons on every pick. shipped:
   `fill` books veryLimited, then limited, then available, ties by
   format and topic fit, and prints the reason on every booking line.
2. repeat sittings as one target. name the talk, try its sittings in
   order, including sittings AWS adds late. one offering held at most once.
3. arrive-by buffer plus in-venue legs. plan to 11 minutes before start
   and account for floors and areas inside large venues (encore vs wynn,
   promenade sides at caesars).
4. walk and leave-now blocks on the official schedule. personal-time
   entries make travel visible where the week is actually read. charset
   and timezone traps are documented in `docs/api-field-notes.md`.
5. re-runnable plan ids plus resume on unknown outcomes. `--dry-run`
   output becomes an artifact a later run can apply, and the
   cancel-then-book path gets a tested rollback for the double-failure case.
6. watcher cron live on rocm-aibox. install the timer from
   `docs/daily-new-sessions.md` and calendar the monthly re-login
   (refresh tokens last 30 days).

## next (bigger)

7. session notes plus post-event trip report. a notes file per reserved
   session, then a report stitching notes to real abstracts with explicit
   slots for bryan's own takeaways.
8. day-by-time availability grid. the open-windows table in
   `docs/mcp-approach.md` as a grid: days across, times down, bands
   instead of invented counts.
9. per-operation quota buckets plus an empty-catalog guard. batch sizes
   from quota left, stop after one retry-after. required before any loop
   or shared use.
10. group views from busy ranges only. shared sessions, meetup slots,
    team split-coverage. needs the backend we do not have; the shape is
    specced in `docs/hallway-windows.md` (meetup slots are the solo version).
11. own MCP server plus hosted demo. local catalog and schedule, gated
    writes, no model. stack order when extending: rust over python,
    firecracker-functions over hosted services, MCP last. rust on
    graviton if functions are needed. webp motion for
    bryanchasko.com/reinvent-26 follows stills, per brand.

## declined

- multilanguage output. quality cannot be judged in a second language;
  unjudgeable output does not ship.
- continuous auto-snag polling. hand-run `fill` stays the default;
  revisit on site with a laptop awake.
