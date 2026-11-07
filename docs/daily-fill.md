# daily fill: catch released seats

popular reserved sessions fill within days of seating opening. seats come back when people cancel. `reinvent26 fill` checks only the sessions that fit your free windows and books the best one per window

## what it does

- reads your live schedule. reserved seats are fixed points
- finds reservable catalog sessions that fit between held seats under the venue-gap rules in data/reinvent2026/map-config.json (same venue 0 min, strip cluster 30 min, anything involving mgm grand 60 min)
- drops bedrock and frontier-model sessions, and skips repeats of a session you already hold
- live-checks seatAvailability only for those candidates. GetSession is the only call that returns it
- books scarcest seats first (veryLimited, then limited, then available); ties break by format (workshop first), then topic fit. every booking prints its reason: seat band, format, topic match, start time. re-checks fit after every booking. retries a `other` failure once
- writes the resulting schedule to .cache/reinvent2026/schedule.json

## fail fast

| check                             | behavior                                                 |
| --------------------------------- | -------------------------------------------------------- |
| no catalog on disk                | exit 2 before any api call                               |
| no valid token                    | exit 2, prints the login command                         |
| 12-session probe slower than 30 s | exit 3, try later                                        |
| per-run cap                       | `--max-checks` (default 400) bounds the live seat checks |

## run on demand

```
cd cli
python3 -m reinvent26 fill --dry-run    # report only
python3 -m reinvent26 fill              # book
```

typical run on 2026-10-29: 100 fitting candidates checked in about 20 s

## run daily (optional, for other attendees)

reference setup for readers who want automation. it is not installed on the author's machine. the author runs fill by hand

```
# ~/.config/systemd/user/reinvent26-fill.service
[Unit]
Description=reinvent26 fill: book released re:Invent seats

[Service]
Type=oneshot
WorkingDirectory=%h/code/<path-to-repo>/cli
ExecStart=/usr/bin/timeout 180 /usr/bin/python3 -m reinvent26 fill
```

```
# ~/.config/systemd/user/reinvent26-fill.timer
[Unit]
Description=reinvent26 fill twice daily

[Timer]
OnCalendar=*-*-* 07,19:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```
systemctl --user daemon-reload
systemctl --user enable --now reinvent26-fill.timer
journalctl --user -u reinvent26-fill -n 20
```

cron alternative:

```
0 7,19 * * * cd ~/code/<path-to-repo>/cli && timeout 180 python3 -m reinvent26 fill >> ~/.cache/reinvent2026/fill.log 2>&1
```

## swaps (manual, judgment call)

fill never cancels. to trade two chalk talks for one workshop that overlaps them:

- re-check the workshop's seat live first
- cancel the chalk talks, book the workshop
- if the booking fails, rebook the chalk talks right away

on 2026-10-29: AIM318 replaced AIM433 + STG338-R (mon, mgm), and SEC318-R1 replaced IND322-R + IND3304-R1 (tue, wynn)
