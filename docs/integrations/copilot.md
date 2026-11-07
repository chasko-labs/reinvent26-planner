# Microsoft Copilot with the AWS Events MCP server

three routes reach the Events server at `https://api.awsevents.com/mcp`.
pick the one matching where you work.

## route 1: Copilot Studio agent

[Copilot Studio takes MCP servers](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
as agent actions through the connector infrastructure:

1. in Copilot Studio, open your agent, select add an action, and search
   for your MCP server (or build a
   [custom connector in Power Apps](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
   pointing at the URL above with OAuth).
2. sign in with Builder ID when the connector prompts; requested scopes
   are `openid email events/access`.
3. test with list events, then your schedule, before any reserve or
   favorite action.

this needs a Copilot Studio maker license and suits a team agent.

## route 2: GitHub Copilot in VS Code

1. open the command palette and run MCP: Add Server. choose an HTTP
   server and paste `https://api.awsevents.com/mcp` (workspace
   `.vscode/mcp.json` or user config). the file shape is:
   `{"servers": {"awsevents": {"type": "http", "url": "https://api.awsevents.com/mcp"}}}`.
2. enable the server for GitHub Copilot agent mode and sign in with
   Builder ID on first call (VS Code 1.101 or newer handles the OAuth flow).

## route 3: Microsoft 365 admin

Microsoft 365 Copilot supports admin-registered
[custom federated connectors](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/set-up-custom-federated-connectors)
backed by an MCP server. this is an administrator operation (Global or
AI admin role); the base URL is the same one above.

## confirm it works

list events (`reinvent2026` comes back), then your schedule. work from
the handoff block at the bottom of
`docs/new-sessions/new-sessions-<date>.md` the same way
`docs/integrations/kiro-cli.md` describes.
