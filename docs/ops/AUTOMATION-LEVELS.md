# Automation Levels

This document defines how aggressively ATLAS should reduce manual work while keeping repo ownership and retention explicit.

## Level 0: Observe

ATLAS reads doctrine, audits, and repo state, but it does not write previews, memory artifacts, commits, or PRs.

Use when:

- the task is an audit only
- repo ownership is unclear
- the operator wants a manual-only pass

## Level 1: Structured Handoff

ATLAS captures task results as a validated handoff JSON and stops there.

Required outputs:

- handoff under `runtime/receipts/handoffs/`
- schema validation result

## Level 2: Preview Automation

ATLAS consumes the handoff and prepares repo-targeted preview artifacts without mutating git.

Required outputs:

- target repo detection result
- commit preview JSON and commit message under `tmp/previews/`
- PR preview JSON and rendered markdown under `tmp/previews/`

This is the default operating level for cross-session handoff reduction.

## Level 3: Repo Mutation

ATLAS is allowed to execute repo-local git actions when repo permissions and auth allow it.

Allowed actions:

- `git add -A` when explicitly requested
- `git commit -F <preview message file>`
- `gh pr create` from the resolved repo root

Required rules:

- detect the actual owning repo first
- preview first
- fail clearly when `.git` access or remote auth is blocked
- never treat `C:\ATLAS` as the commit target

## Level 4: Stack Memory And Retention

ATLAS continuously reduces manual rereading and runtime clutter at the stack layer.

Allowed actions:

- extract normalized memory from approved docs into `runtime/cortex/catalog/memory/`
- compact stale previews and expired temp files
- archive redundant derived artifacts and superseded timestamped receipts
- emit retention reports

Required rules:

- do not invent facts during memory extraction
- keep provenance back to the source doc
- never auto-delete repo source, raw imports, or source-of-record docs

## Current Target State

ATLAS should operate at:

- Level 2 by default for Codex handoff flows
- Level 3 when the operator explicitly chooses execution and the repo checkout allows it
- Level 4 for stack-owned memory extraction and retention maintenance

## Near-Zero-Manual Definition

Near-zero-manual in ATLAS does not mean hidden mutation. It means:

- repo-target detection is automatic and inspectable
- commit and PR text are generated automatically from structured handoffs
- execution paths fail fast with a concrete reason instead of silent drift
- stack memory and retention reduce repeated operator cleanup work
