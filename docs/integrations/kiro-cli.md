# kiro-cli with the AWS Events MCP server

verified 2026-11-05 against [kiro.dev](https://kiro.dev/docs/mcp/) and the
[AWS Events MCP docs](https://docs.aws.amazon.com/events/latest/devguide/mcp-server.html).
local kiro-cli here: 2.37.1 (`~/.local/bin/kiro-cli`); current line is 3.x.

## install

one line per platform ([downloads](https://kiro.dev/downloads/)):

```
# macOS or Linux
curl -fsSL https://cli.kiro.dev/install | bash

# macOS Homebrew
brew install --cask kiro-cli
```

Ubuntu uses a `.deb` from the downloads page; Windows 11 uses the
installer there. then:

```
kiro-cli --version   # 3.x is current; `kiro-cli update` moves 2.x installs over
kiro-cli diagnostic  # version, system info, environment
```

sign in when prompted (`https://app.kiro.dev` account). kiro-cli needs a
browser for its own auth, same as the Events sign-in below.

## add the Events MCP server

put this in your user MCP config (`~/.kiro/settings/mcp.json`), merging
with what is there — values verbatim from the AWS docs:

```json
{
  "mcpServers": {
    "awsevents": {
      "url": "https://api.awsevents.com/mcp",
      "oauth": {
        "clientId": "7vmom55m1qstvq8i71ph127bfq",
        "redirectUri": "http://127.0.0.1:8976",
        "oauthScopes": ["openid", "email", "events/access"]
      }
    }
  }
}
```

end `redirectUri` at the port: kiro appends `/oauth/callback` itself, and
a value with a path falls back to a random port that cannot sign in.
restart kiro-cli (or reload the window) after editing.

## sign in and confirm

1. ask kiro-cli to list events. the first call opens the Builder ID
   sign-in in your browser (loopback to `127.0.0.1:8976`, so sign in on
   the machine kiro-cli runs on).
2. confirm: `list events` returns `reinvent2026`, and asking for your
   schedule shows your favorites and reservations. registration for
   re:Invent 2026 is required for the catalog and any schedule call.

## use it with the watcher handoff

`python3 -m reinvent26 new-sessions` writes a report ending in a handoff
block (`docs/daily-new-sessions.md`). paste that block into kiro-cli:
it names the exact session ids, what clashes, and that `GetSchedule` is
the source of truth. kiro-cli reserves and favorites through the MCP
server; the watcher only suggests.

rules both sides follow: `skills/awsevents-muse/SKILL.md`.
