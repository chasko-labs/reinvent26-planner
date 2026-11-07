# daily new sessions: watcher runbook

`python3 -m reinvent26 new-sessions` diffs the live catalog against the
cache, evaluates added sessions with the local model, and writes a dated
report plus a handoff prompt for kiro-cli with the Events MCP server.
read-only against the api: it never reserves, favorites, or writes
personal time. the handoff is the only thing that changes a schedule,
and a person pastes it.

## what it records

- added sessions since the last snapshot (by session id) and removed ones.
  "new" here means newly published or late-added sessions, including
  sessions whose details were held back until AWS announced them.
- live seat availability for each added session (`GetSession` is the only
  call that returns it), bounded by `--max-checks` (default 100).
- local-model evaluation: the added sessions go to the OpenAI-compatible
  endpoint (`--endpoint`, default `http://127.0.0.1:8181/v1`) with your
  tracked topics from `data/reinvent2026/map-config.json`. unknown codes
  are dropped against the added list. when the endpoint is down the
  report still runs on deterministic topic-tag order and says so.
- launch signals among the added sessions: title (strong) and abstract
  (weak) keyword matches, the same detector that writes
  `docs/launch-ledger.md`. late-added "what's new" sessions show up here.
- conflicts against your live schedule and opportunities that fit under
  the venue-gap rules.

## run it

```
cd cli
python3 -m reinvent26 new-sessions reinvent2026 --dry-run   # print, write nothing
python3 -m reinvent26 new-sessions reinvent2026             # write docs/new-sessions/<date>.md
```

first run with no cache records a baseline and reports everything as
added; the second run is the first real diff. an empty live catalog is
treated as an outage (exit 1, cache untouched), never as "all removed".

## cron on your always-on machine (systemd, twice daily)

ours runs on a home server; yours can be any machine that stays up.
the watcher needs your stored token (`python3 -m reinvent26 login` once;
refresh lasts 30 days, so re-sign-in monthly or the run exits 2). the
local model endpoint is optional; without it the report falls back to
topic tags. replace `<path-to-repo>` with your clone in the units below.

what login prints (captured from the cli on rocm-aibox; values redacted,
each run mints fresh ones):

```
# opening browser for Builder ID sign-in (or open this url):
# https://oauth.awsevents.com/oauth2/authorize?response_type=code
#   &client_id=7vmom55m1qstvq8i71ph127bfq
#   &redirect_uri=http://localhost:8484/callback
#   &scope=openid+email+events/access&identity_provider=AWSBuilderID
#   &code_challenge=<pkce-s256>&code_challenge_method=S256&state=<csrf>
```

sign in with builder id in the browser. the callback lands on
`127.0.0.1:8484` on the machine that ran login, so from a machine
without a browser forward the port first
(`ssh -L 8484:localhost:8484 <host>`). tokens land in
`~/.config/reinvent26/tokens.json` (refresh: 30 days).

```
# ~/.config/systemd/user/reinvent26-new-sessions.service
[Unit]
Description=reinvent26 new-session watcher

[Service]
Type=oneshot
WorkingDirectory=%h/<path-to-repo>/cli
ExecStart=/usr/bin/timeout 600 /usr/bin/python3 -m reinvent26 new-sessions reinvent2026
```

```
# ~/.config/systemd/user/reinvent26-new-sessions.timer
[Unit]
Description=reinvent26 new-session watcher twice daily

[Timer]
OnCalendar=*-*-* 07,19:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```
systemctl --user daemon-reload
systemctl --user enable --now reinvent26-new-sessions.timer
journalctl --user -u reinvent26-new-sessions -n 20
```

cron alternative:

```
0 7,19 * * * cd ~/<path-to-repo>/cli && timeout 600 python3 -m reinvent26 new-sessions reinvent2026 >> ~/.cache/reinvent26/new-sessions.log 2>&1
```

read `docs/new-sessions/new-sessions-<date>.md`, then paste the handoff
block at the bottom into kiro-cli (setup: `docs/integrations/kiro-cli.md`).
kiro-cli makes the changes through the Events MCP server; the watcher
only ever suggests.
