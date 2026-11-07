# sign in: Builder ID for the Events API

everything that touches your schedule — and every MCP tool call —
runs as you, through Builder ID OAuth with PKCE. one sign-in covers
the cli, the MCP server, and the watcher cron.

## step zero: identify your environment

you run every check below before any other command. each answer
decides what you do next:

```
hostname; uname -s
# Darwin = a Mac. Linux = a home server or cloud box. ours read
# "macmini + Darwin" and "rocm-aibox + Linux".
# tokens land on the machine you sign in on, so this answer picks
# which sign-in feeds the nightly watcher and which one stays local.

python3 --version
# want 3.10 or newer. macs ship no `python` command at all, so you
# must type `python3`, never `python`. if Python 3 is missing
# entirely: `brew install python` (or python.org), then re-check.

git remote -v
# run inside the repo. want chasko-labs/reinvent26-attendee-planner.
# any other URL means a stale clone. stop and reclone before you
# trust any output from it.

git status --short --branch
# want main, clean. a different branch or modified files means you
# are not looking at the code you think you are.

python3 -m reinvent26 status reinvent2026
# run from the cli/ directory. it reports sign-in state and never
# prints secrets. this is always the first planner command.
```

the cli is stdlib-only: no pip install, no virtualenv. nothing
else is required to run it.

## mac procedure: update then verify

`<repo>` below means your clone of the planner (ours lives at
`~/Code/chasko-labs/reinvent26-planner` on the Mac and
`~/code/chasko-labs/reinvent26-planner` on the home server).
you run every step below in order, in a local Terminal window on
your Mac. you run nothing over ssh until step 6.

1. open Terminal on your Mac. open a local window, not an ssh session.
2. go to the repo. you run `cd <repo>`. running `git pull` anywhere else fails with "not a git repository".
3. confirm the remote. you run `git remote -v`. you must see `chasko-labs/reinvent26-attendee-planner`. any other URL means a stale clone. stop and reclone.
4. update. you run `git pull`. you expect "Already up to date" or a short fast-forward list.
5. verify the cli loads. you run `cd cli && python3 -m reinvent26 status reinvent2026`. you expect a sign-in line, an api reachability line, and a schedule line. any `command not found: python` means you typed `python` instead of `python3`.
6. open a second terminal tab for the always-on machine. you run `ssh -L 8484:localhost:8484 YOU@YOUR-BOX`. you land in that machine's start directory, which is usually not the planner. you stay in this session for steps 7 to 9.
7. go to the planner repo, then sign in. you run `cd <repo>/cli && python3 -m reinvent26 login`. the tilde path works from any start directory. the command prints a URL.
8. approve in your Mac browser. you open the printed URL, sign in with Builder ID, and approve. the callback travels back through the ssh tunnel.
9. confirm on the box. you run `python3 -m reinvent26 status reinvent2026`. you expect `signed in` and `schedule readable`. you then type `exit` to close the ssh session.

## the bare-python mistake (recorded, not repeated)

earlier versions of these docs said `python -m`. that fails on both
machines: macOS ships no `python`, and neither does the box. every
command now reads `python3 -m`. the pre-push gate rejects bare
`python -m` in cli, docs, demo, mock, and the readme, so the mistake
cannot return through a normal push.

## how to tell if you are signed in

three answers, each naming the fix:

- `signed in: access token live until ...` — good for the hour shown.
  below it: `schedule readable: N reserved, M favorites` proves the
  sign-in carries your registration.
- `signed in: expired access token refreshed just now` — good; the
  30-day refresh did its job silently.
- `signed out: ...; run python3 -m reinvent26 login` — the refresh is
  dead (older than 30 days or revoked). the schedule line will read
  `schedule unreadable (401): sign in first`. sign in again.

manual check without the command: `stat ~/.config/reinvent26/tokens.json`
shows the last sign-in date. older than 30 days means the refresh is
dead — `status` will confirm it in one line.

## the login in plain english

Builder ID sign-in ends with your browser handing a code to a tiny
web server the cli runs on your own machine at
`http://127.0.0.1:8484/callback` (it tries 8484 through 8489 and
prints the one it got). so the machine that runs `login` must be the
machine whose browser approves it — or be connected to it by a tunnel:

```
ssh -L 8484:localhost:8484 YOUR-AIBOX-SSH-HOST
```

read it as: ssh to your box, and wire port 8484 on your Mac's
localhost to port 8484 on the box's localhost. the callback the box
listens for arrives through that wire. YOUR-AIBOX-SSH-HOST is
whatever you normally ssh to — the same name or address already in
your ssh config. `<aibox>` is a placeholder, never typed literally,
and ssh with no destination always prints usage.

## path 1: hotel laptop, everything local (Vegas)

no tunnel needed. the browser and the callback live on one machine:

```
cd <repo>/cli
python3 -m reinvent26 login
```

a browser tab opens (or the cli prints a URL — open it). sign in
with Builder ID, approve, back in the terminal:

```
python3 -m reinvent26 status reinvent2026
# signed in: access token live until ...
# schedule readable: N reserved, M favorites
```

tokens land in `~/.config/reinvent26/tokens.json` on that laptop.

## path 2: home powerdesktop does the work, hotel consumes it

this is bryan's setup. the desktop at home runs the watcher cron and
holds the tokens; the hotel laptop holds no credentials at all:

1. from the Mac on the home network, open the tunnel and sign in on
   the box (the login above, run over ssh). tokens stay on the box.
2. the box generates `docs/new-sessions/new-sessions-<date>.md`
   twice daily on its own.
3. at the hotel, read the report and paste its handoff block into
   Meta Muse (`docs/integrations/meta-muse.md`) for planning, or
   into laptop kiro-cli (`docs/integrations/kiro-cli.md`) for live
   seat changes. the report travels; the tokens never leave home.

## lifetimes

| token   | lasts   | renews                   |
| ------- | ------- | ------------------------ |
| access  | 60 min  | silently, on any command |
| refresh | 30 days | never — sign in again    |

when a command fails with 401 it already tried one silent refresh;
a second 401 means the refresh is dead, not that you should retry.

## what the errors mean

- `401 sign in first` — no usable token. `status`, then `login`.
- `403` — signed in fine, but this Builder ID is not registered for
  the event. signing in again changes nothing; register on the
  re:Invent site.
- `409` — the operation is closed on the API side right now, not a
  bad request. retry later.
- `429` — quota spent; the cli already honored one Retry-After.
  wait before retrying.
