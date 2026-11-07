# Google Gemini with the AWS Events MCP server

two places accept the Events server: the Gemini web app and Gemini CLI.

## Gemini web app: custom apps

open [gemini.google.com](https://gemini.google.com), then settings and
help, then Connected Apps. under custom apps, add a custom app and paste
the MCP server URL:

```
https://api.awsevents.com/mcp
```

sign in with your Builder ID when prompted (scopes
`openid email events/access`).

connect from gemini.google.com with a personal Google account (18 or
over, US, Keep Activity on, English). write actions ask for your
confirmation.

confirm: ask Gemini to list events (`reinvent2026` should come back),
then ask for your schedule.

## Gemini CLI

```
gemini mcp add --transport http awsevents https://api.awsevents.com/mcp
gemini mcp list    # confirm it is registered
```

then sign in with `/mcp auth` inside the CLI session and ask it to list
events. the CLI runs on your machine, so the Builder ID loopback
sign-in behaves like kiro-cli's: sign in on the machine the CLI runs on,
with a browser available.

## which to use

the web app needs no install and fits quick schedule checks; the CLI fits
the watcher workflow — paste the handoff block from
`docs/new-sessions/new-sessions-<date>.md` the same way
`docs/integrations/kiro-cli.md` describes, replacing only the tool names
with what Gemini lists for the connector.
