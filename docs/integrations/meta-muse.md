# Meta Muse with the AWS Events MCP server

verified 2026-11-05 in Muse chat: connector added by URL, client ID
entered, error captured, public list read back.

## what works with no sign-in: the public event list

add the custom connector with URL `https://api.awsevents.com/mcp` and
ask for events. `ListEvents` needs no sign-in and returns the ongoing
and upcoming events — on 2026-11-04 that was exactly two:

- `reinvent2026` — re:Invent 2026, Las Vegas, Nov 30–Dec 4
  (America/Los_Angeles). flagged authentication-required: the event
  lists, but its session catalog and every schedule call refuse
  unsigned callers.
- `Cohort-CloudBuenosAires-2026` — AWS Cloud and AI Day, Buenos Aires.
  no authentication required.

anything under `reinvent2026` beyond the event row — sessions, seat
bands, favorites, reservations, personal time — answers 401
("Sign in to continue") without a signed-in, registered attendee.
no sessions, no counts, no seat data. the same public call works from
the cli with no token at all:

```
cd cli
python3 -m reinvent26 events
python3 -m reinvent26 status
```

or run the bundled no-token demo: `python3 demo/demo_public.py`.

## authenticated connector: blocked at sign-in (observed)

entering the shared public client ID `7vmom55m1qstvq8i71ph127bfq`
in the connector's Client ID field returns "An error was encountered
with the requested page." the connector registers holding no
credential, so setup never completes. AWS's own OAuth endpoint names
the cause:

```
https://oauth.awsevents.com/error?error=redirect_mismatch&client_id=7vmom55m1qstvq8i71ph127bfq
```

`redirect_mismatch`: AWS matched Muse's hosted callback
(`https://agent.meta.ai/api/hatch/oauth/callback`) against its
registered callbacks, found only loopback ports 8484–8489, and
rejected it. screenshots reviewed 2026-11-04 (macmini desktop,
11:40–12:06): Client ID screen, the error page, and Muse confirming
`custom.awsevents` holds no credential. booking, favorites, and
schedule reads from inside Muse stay blocked until either side
changes. do not retry the same entry — it fails the same way.

## the pattern that works today

authenticated work happens on a machine you own; Muse plans from the
output. local booking goes through laptop kiro-cli
(`docs/integrations/kiro-cli.md`), which can use the loopback
callback.

finding bryan works with no connector at all. paste the current
week into Muse and ask where the gaps are — the artifacts:

- `docs/hallway-windows.md` — morning, midday, and evening gaps plus
  breakfast, lunch, and dinner windows, built from the live schedule.
  this is the "can he make breakfast / lunch / dinner / re:Play"
  answer.
- `docs/new-sessions/new-sessions-<date>.md` — newest sessions with
  live seats, conflicts against his week, and a handoff block.
- `docs/launch-ledger.md` — which sessions signal launches.

all three are plain text in this repo: paste them into any Muse chat
and ask "where can I find him for lunch Thursday" or "which of these
fits around his held seats". no sign-in on the reader's side, no
coordinates shared — venue names and windows only.
