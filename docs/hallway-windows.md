# hallway windows: where the week has air

when to find bryan outside a session room: breakfast, lunch, dinner, and
the morning / midday / evening gaps between held seats. snapshot from the
live schedule on 2026-10-30 (14 reserved seats); rooms and times move, so
regenerate before the event. no multilanguage anything: english only.

## how to regenerate

```
cd cli
python3 -m reinvent26 schedule reinvent2026          # current held seats
python3 -m reinvent26 slots reinvent2026 --window 2026-12-01T08:00:00,2026-12-01T12:00:00
python3 -m reinvent26 fill --dry-run                 # what still fits
```

a window below is real only if it survives the venue-gap rules in
`data/reinvent2026/map-config.json` (same venue 0 min, strip cluster
30 min, anything involving mgm grand 60 min). the 10-minute
reserved-seat rule applies: be in the room 10 minutes before start.

## monday 11-30 — mgm grand all day

held: 08:30 chalk, 11:30 chalk, 13:00 chalk, 15:00-17:00 workshop.
all four at mgm, no cross-strip travel.

- breakfast: before 08:30, mgm side. tight, keep it near the venue.
- midday: 09:30-11:30 between sessions (mgm, no travel owed).
  15 fitting sessions read full on 10-30, so treat this as hallway time,
  not a booking window. good slot for builder chats inside mgm.
- lunch: squeezed. 12:30-13:00 is the only gap and cmp340 starts 13:00,
  so eat near the 13:00 room or skip to an early dinner.
- evening: 17:00 on, mgm side. dinner window, no travel debt.

## tuesday 12-01 — wynn plus caesars forum

held: 12:00 chalk (wynn), 15:00 chalk (forum), 16:30 chalk (wynn).
morning completely open.

- morning: 08:00-12:00 free, wynn side. the biggest unstructured block of
  the week. breakfast plus hallway chats, or a walk-up session that fits
  before the 12:00 chalk (2 candidates read full on 10-30; check live).
- lunch: 13:00-15:00 window between wynn and forum. 11 candidates read
  full on 10-30. eat between venues, then walk to the forum.
- evening: 17:30 on, wynn side. dinner window.

## wednesday 12-02 — mgm plus caesars forum

held: 08:00-10:00 workshop (mgm), 13:30-14:30 chalk (forum),
15:30-17:30 workshop (mgm). a strip crossing each way.

- breakfast: before 08:00, mgm side. tight.
- midday: 10:00-13:30 free, but the forum chalk starts 13:30 and mgm to
  forum needs 60 minutes. leave mgm by 12:30. 45 fitting sessions read
  full on 10-30, so this is expo and hallway time plus an early lunch
  near mgm or en route.
- gap 14:30-15:30 is gap-killed (forum back to mgm for the 15:30
  workshop). travel, not a meeting slot.
- evening: 17:30 on, mgm side. dinner window.

## thursday 12-03 — mgm, wynn, caesars palace

held: 08:00-10:00 workshop (mgm), 12:00-14:00 workshop (wynn),
15:30-17:30 workshop (palace). three venues, the heaviest travel day.

- breakfast: before 08:00, mgm side. tight.
- midday: 10:00-12:00 mgm to wynn. 10 candidates read full on 10-30.
  travel plus a quick bite, not a booking window.
- late lunch: 14:00-15:30 wynn to palace. the only real midday air on
  thursday. eat en route to caesars palace.
- evening: 17:30 on, palace side. dinner window, farthest point from
  home base (venetian).

## friday 12-04 — wynn morning, then open

held: 08:00-10:00 workshop (wynn). nothing after.

- breakfast: before 08:00, wynn side. tight.
- midday and evening: 10:00 on is completely open. the best builder-
  meetup half-day of the week: lunch anywhere, hallway chats with no
  travel debt, dinner wherever the group lands.

## best meetup bets, ranked

1. friday after 10:00. no constraints at all.
2. tuesday 08:00-12:00. four free morning hours on the wynn side.
3. wednesday 10:00-12:30. expo plus hallway before the forum crossing.
4. monday 09:30-11:30. inside mgm, zero travel.
5. thursday 14:00-15:30. en route wynn to palace, late lunch.

every window above was live-checked on 2026-10-30 and every fitting
session read full. recheck seats before inviting anyone to anything:
a full window is a hallway, an open seat is a plan change.
