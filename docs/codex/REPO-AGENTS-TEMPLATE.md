# Repo `AGENTS.md` Template

Use this template when standardizing active ATLAS repos.

```md
# <Repo Name> Rules

Scope
- Applies inside `<repo-path>`.
- Inherits the ATLAS root rules from `../AGENTS.md` only where those rules do not conflict with this repo.

Purpose
- This repo owns `<one-sentence purpose>`.
- Keep this file focused on actionable rules for safe work in this repo.

Routing
- Work that only affects this repo should stay inside this repo.
- Cross-repo changes require naming the other repo ids explicitly.
- Do not edit stack-level standards from here unless the task is specifically about stack governance.

Path Discipline
- Prefer repo-relative paths in docs and config.
- Do not commit machine-specific absolute paths.
- Route retained runtime state to `../../runtime/<repo-id>` when a stack-level state path exists.
- Route disposable outputs to `../../tmp/<class>` when practical.

Repo Baseline
- Keep `README.md` current.
- Keep `.codex/config.toml` present and valid.
- Document the canonical verify command in both this file and the README.

Verification
- Canonical verify command: `<command>`
- Optional strict verify command: `<command>`
- Run verify before claiming completion for code changes.

Workflow Reporting
- If this repo participates in a stack with a root-owned workflow response contract, preserve that root reporting contract instead of redefining a conflicting one here.
- Keep repo-local additions focused on repo-specific verification and scope boundaries.

Do Not Commit
- `.env`
- `.env.*`
- local runtime state
- local logs, screenshots, and scratch files unless the repo explicitly owns them as fixtures

Escalation
- Ask before structural moves, dependency overhauls, secret handling changes, or data migrations.
```

## Required Fields To Fill In

- repo name
- repo path
- repo id
- one-sentence purpose
- canonical verify command
- optional strict verify command
