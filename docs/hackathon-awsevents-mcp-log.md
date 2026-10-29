# hackathon log: awsevents mcp integration

## 2026-10-04 session 1

### goal
wire the aws events mcp server (api.awsevents.com/mcp) into the haunting stack so subagents can plan re:invent 2026 sessions through mcp tools.

### constraints
- rocm-aibox is headless linux. no browser.
- device-code grant not supported by the events api oauth endpoint (confirmed from docs).
- must use authorization code + pkce s256 with ssh tunnel for browser callback.
- tokens go to ssm parameter store (account 211125425201, namespace /heraldstack/shared/awsevents/*), never to local files.
- bridge launcher must be stdio on agent side, streamable http to api.awsevents.com/mcp, injecting bearer from ssm.
- mcp-transport-discipline: spawned agents only see stdio bindings.

### reference implementation
auth.py in cli/reinvent26/ has working pkce flow:
- opens browser to authorize url
- listens on 127.0.0.1:8484..8489/callback
- exchanges code for tokens
- stores to keychain or 0600 file (file storage NOT acceptable here)

### design decisions

#### token storage: ssm parameter store
- access token: /heraldstack/shared/awsevents/access-token (expires in 60 min)
- refresh token: /heraldstack/shared/awsevents/refresh-token (expires in 30 days, rotates on refresh)
- token expiry: /heraldstack/shared/awsevents/token-expires-at (unix timestamp)

ssm is the canonical storage per governance/secret-handling. no ~/.secrets, no .env, no local files.

#### login flow: ssh tunnel + browser on mac mini
1. bryan opens ssh tunnel from mac mini: `ssh -L 8484:localhost:8484 rocm-aibox`
2. on rocm-aibox: `awsevents-mcp-login` prints authorize url and listens on 127.0.0.1:8484
3. bryan opens url in browser on mac mini, signs in with builder id
4. callback arrives at localhost:8484 on mac mini, tunnels to rocm-aibox
5. login helper exchanges code for tokens, stores to ssm

#### bridge launcher: supergateway + ssm token fetch
- stdio on agent side via supergateway
- streamable http to https://api.awsevents.com/mcp
- bearer token fetched from ssm at each invocation (no caching in bridge)
- silent refresh when access token expired: fetch refresh token from ssm, call token endpoint, store new tokens

#### mcp transport
- settings/mcp.json uses ./mcp-launchers/run.sh (dispatcher pattern)
- run.sh finds the bridge script in heraldstack-mcp/launchers/bridges/
- registry.yaml entry documents the server

### implementation steps

1. create login helper: awsevents-mcp-login (python script using stdlib, stores to ssm)
2. create refresh helper: awsevents-mcp-refresh (silent refresh, called by bridge)
3. create bridge launcher: awsevents-bridge.sh (stdio -> streamable http, fetches token from ssm)
4. add registry.yaml entry
5. add mcp.json entry
6. create runbook at docs/runbooks/awsevents-mcp-login.md
7. test: bryan logs in, then call ListEvents through mcp

### what failed
- device code grant: not supported by the events api oauth endpoint. confirmed from docs at https://docs.aws.amazon.com/events/latest/devguide/mcp-server.html

### commands run
```bash
# checked hs-secret tool
which hs-secret && hs-secret --help

# read reference auth implementation
cat cli/reinvent26/auth.py

# read bridge patterns
cat ~/code/heraldstack/heraldstack-mcp/launchers/bridges/s3vectors-bridge.sh
cat ~/code/heraldstack/heraldstack-mcp/launchers/bridges/context7-bridge.sh

# read registry and mcp.json
cat ~/code/heraldstack/heraldstack-mcp/registry.yaml
cat ~/code/heraldstack/haunting-kiro-cli/.mcp.json
```


### files created

| file | purpose |
| --- | --- |
| bin/awsevents-mcp-login | login helper (tunnel-aware, stores tokens to ssm) |
| bin/awsevents-mcp-refresh | silent token refresh (called by bridge) |
| ~/code/heraldstack/heraldstack-mcp/launchers/bridges/awsevents-bridge.sh | stdio bridge to streamable http endpoint |
| ~/code/heraldstack/heraldstack-mcp/docs/runbooks/awsevents-mcp-login.md | runbook for bryan |
| ~/code/heraldstack/heraldstack-mcp/registry.yaml | added awsevents entry |
| ~/code/heraldstack/haunting-kiro-cli/.mcp.json | added awsevents server entry |

### verified

- kiro-doctor check mcp-paths: pass (14 servers, all absolute launcher paths)
- python syntax: both helpers compile without errors
- bash syntax: bridge script passes `bash -n`
- supergateway: v3.4.3 available at ~/.nvm/versions/node/v24.14.0/bin/supergateway

### next step

bryan must complete browser sign-in. the session is waiting for him to run the login helper.


### bryan sign-in required

the integration is ready. bryan must complete the browser sign-in to store tokens to ssm.

