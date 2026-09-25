# contributing to reinvent26-planner

## fastest path: pair with Muse Code

1. Install Muse Code and open this repo.
2. The repo ships an agent skill at `skills/awsevents-muse/SKILL.md`. Point your
   agent at it before touching any API code. It covers the rules that are easy
   to get wrong: paginate `ListSessions` until `nextToken` is absent, first
   pass with `includeAbstracts=false`, 1-10 ids per write, per-session result
   inspection, GetSchedule as source of truth, the 409 gate until 8 Oct 2026,
   and write reconciliation after timeouts.
3. Pick an issue and hand it over verbatim, e.g. "implement issue #7 following
   the repo skill". One issue equals one PR; never mix units.

## MCP servers worth connecting

- `awsevents` at `https://api.awsevents.com/mcp` (streamable HTTP, PKCE, public
  client id in the skill). Every tool call needs sign-in, including catalog
  reads. Best for interactive planning sessions.
- A read-only Amazon Web Services path for stack-aware work (`[utility]`
  issues). Keep the agent read-only via IAM condition keys even if your own
  role can write.
- Optional local model pass over cached catalog json (see
  `docs/local-models.md`). The API stays source of truth; the model only
  ranks. Never send access tokens to a model process.

## ground rules

- Python is stdlib-only, 3.11+. The rust helper (`rust/catalog-filter`) is
  zero-dependency. Do not add a dependency without opening an issue first.
- Every behavior change ships with a test: `python3 -m pytest -q` and
  `cargo test --manifest-path rust/catalog-filter/Cargo.toml` stay green.
- API-touching PRs paste a live CLI transcript (or the 409/403 the gate
  produced) plus the GetSchedule confirmation for writes.
- Session fields are optional in this API. New code must tolerate missing
  fields the way `schedule.summarize` does.
- Never commit tokens, credentials, or `.cache/` contents. `.cache/` is
  gitignored; public catalog json samples for tests live in `tests/`.
- Error behavior per the skill: 403 with a body means not registered (say so,
  do not retry), 429 honors Retry-After, writes reconcile via GetSchedule
  instead of blind retry.

## PR shape

- Title starts with the issue bracket and number, e.g. `[utility] slots
command (#8)`.
- Body: what changed, the validation commands run, and the observed result.
- Keep the README accurate: if your change adds a command or flag, document
  it in the same PR.
