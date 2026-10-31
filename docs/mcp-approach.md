# planning reinvent 2026 through the events mcp (and the cli behind it)

snapshot of the live approach as of 2026-10-30. the api stays source of
truth; everything below was read back from `GetSchedule` and `GetSession`,
never assumed from a 200.

## the two interfaces

- interactive agent sessions: the awsevents mcp server at
  `https://api.awsevents.com/mcp` (streamable http, pkce, public client id
  in `skills/awsevents-muse/SKILL.md`). every tool call needs sign-in,
  including catalog reads.
- scriptable work: the python cli in `cli/` (plain rest). public
  `ListEvents` needs no sign-in; catalog reads plus all schedule writes
  need a bearer token and event registration.

both speak the same api. the skill (`skills/awsevents-muse/SKILL.md`) is
the rulebook both sides follow.

## sign-in from a headless host

`rocm-aibox` has no browser, and the events oauth endpoint has no device
grant, so sign-in rides an ssh tunnel from the browser machine:

1. on the mac: `ssh -L 8484:localhost:8484 rocm-aibox`
2. on the host: `bin/awsevents-mcp-login` prints the authorize url and
   listens on `127.0.0.1:8484`
3. sign in with builder id in the mac browser; the callback tunnels back
4. tokens land in ssm parameter store
   (`/heraldstack/shared/awsevents/*`, account 211125425201), never in files

`bin/awsevents-mcp-refresh` serves tokens to both surfaces: reads try the
sso profile then fall back to the roles-anywhere `ops-reader` profile, and
a write failure still returns the fresh access token in memory for that
run. the mcp bridge (`awsevents-bridge.sh` via supergateway) fetches a
token from ssm per invocation and refreshes silently on expiry.

## the mcp walkthrough, in call order

1. `ListEvents` — confirm `reinvent2026` is visible.
2. `ListSessions` with `includeAbstracts=false`, following `nextToken`
   until absent. a short page is not the last page.
3. shortlist by topic/level locally, then `GetSession` for abstracts and
   `seatAvailability` on the shortlist only. `GetSession` is the only call
   that returns seat availability.
4. `favorite` the plan in batches of 1-10. favorites record interest;
   they do not reserve seats.
5. `GetSchedule` — the only confirmation that counts. http 200 on a batch
   never implies every session succeeded; inspect each per-session result.
6. `reserve` 1-10 ids per call (409 before 8 oct 2026 means retry after
   reopen, not a bad request), then `GetSchedule` again.
7. on any unknown write outcome (timeout, 500, 503): never blind-retry.
   read the schedule, compare with intent, submit only what remains.
   404 on cancel/remove means already absent: complete.

## the scriptable mirror

```
cd cli
python -m reinvent26 login
python -m reinvent26 sessions reinvent2026            # full pull, cached
python -m reinvent26 shortlist reinvent2026 --topics agents,mcp --level 3 --top 20
python -m reinvent26 schedule reinvent2026            # clashes included
python -m reinvent26 slots reinvent2026 --window 2026-12-01T13:00:00,2026-12-01T16:00:00
python -m reinvent26 map                              # docs/event-map.md + launch ledger
python -m reinvent26 fill --dry-run                   # what fits, books nothing
python -m reinvent26 fill                             # book open seats, single pass
```

seat-aware planning (`seats.py`, `mapper.py`, `fill.py`):

- sweep `seatAvailability` across the reservable catalog; only
  `available`/`limited`/`veryLimited` count as bookable.
- venue travel gaps from `data/reinvent2026/map-config.json`: 0 min same
  venue, 30 min inside the strip cluster
  (venetian, wynn/encore, caesars palace, caesars forum), 60 min to or
  from mgm grand.
- logistics first, subject second: a session must fit a free window under
  the gap rules before topics even rank it. standing exclusions (bedrock
  except nova, frontier-model titles) and repeats of held sessions never
  book. any format books — workshops just rank first.
- `fill` never cancels. `fill --rebalance` re-plans the week and swaps
  toward the plan (re-check live, cancel conflicts, book, rebook originals
  on failure). nothing here runs on a timer; every run is by hand.

## live state: 14 reserved (2026-10-30)

- mon mgm, all four back to back at one venue
  - 08:30 STG363 chalk: modernizing vmware with fsx for netapp ontap
  - 11:30 INV530-R1 chalk: ec2 at 20, rebuilding the control plane live
  - 13:00 CMP340 chalk: drug discovery with braket and q-ctrl
  - 15:00 AIM318 workshop (2h): resilient vlm training on hyperpod
- tue wynn plus caesars forum
  - 12:00 IND359-R1 chalk: in-country hpc seismic data on aws brazil
  - 15:00 IND322-R chalk: physical ai in telecom workload placement
  - 16:30 IND3304-R1 chalk: knfsd file cache, nfs storage into cloud
- wed mgm plus caesars forum
  - 08:00 ANT402-R workshop (2h): redshift data sharing
  - 13:30 INV537 chalk: safe physical interaction without torque sensors
  - 15:30 AIM434-R1 workshop (2h): sagemaker dataset prep to custom model
- thu mgm, wynn, caesars palace
  - 08:00 STG412 workshop (2h): storage bottlenecks for oltp on ebs
  - 12:00 SEC401 workshop (2h): live ddos defense
  - 15:30 MAM416 workshop (2h): freeing .net from windows licensing
- fri wynn
  - 08:00 BIZ321-R1 workshop (2h): connect chat to co-browse/voice/video

## live state: open windows of an hour or more (2026-10-30)

every fitting session below was live-checked the same day; all seats read
`unavailable`.

| Window          | Between                     | Fits live             |
| --------------- | --------------------------- | --------------------- |
| Mon 09:30-11:30 | MGM STG363 → MGM INV530     | 15 sessions, all full |
| Mon 14:00-15:00 | MGM CMP340 → MGM AIM318     | none scheduled        |
| Mon 17:00-18:00 | MGM AIM318 → end            | none scheduled        |
| Tue 08:00-12:00 | start → Wynn IND359         | 2 sessions, both full |
| Tue 13:00-15:00 | Wynn IND359 → Forum IND322  | 11 sessions, all full |
| Wed 10:00-13:30 | MGM ANT402 → Forum INV537   | 45 sessions, all full |
| Wed 14:30-15:30 | Forum INV537 → MGM AIM434   | 24 exist, gap-killed  |
| Thu 10:00-12:00 | MGM STG412 → Wynn SEC401    | 10 sessions, all full |
| Thu 14:00-15:30 | Wynn SEC401 → Palace MAM416 | 2 sessions, both full |
| Fri 10:00-18:00 | Wynn BIZ321 → end           | 15 sessions, all full |

beyond these windows, a fresh sweep on 2026-10-30 found 43 open seats
conference-wide (was 59 that morning; seats are tightening), and every
one clashes with a held seat, repeats one, or is subject-excluded — so
13 was the no-cancel ceiling. the sprint then traded one held workshop
for two chalk talks (sec318-r1 -> ind322-r + ind3304-r1, tue), moving the
line to 14 seats at the same 1260 minutes. past it lies more swaps
(`fill --rebalance`), which cancel first and stay dry-run-first.

## further reading

- skill: `skills/awsevents-muse/SKILL.md`
- call-by-call log: `docs/hackathon-awsevents-mcp-log.md`
- field notes (calls, enums, lessons): `docs/api-field-notes.md`
- event map and launch ledger: `docs/event-map.md`, `docs/launch-ledger.md`
- full-but-interesting (no-seat topics, presenters, youtube flags):
  `docs/full-but-interesting.md`
- daily fill runbook: `docs/daily-fill.md`
