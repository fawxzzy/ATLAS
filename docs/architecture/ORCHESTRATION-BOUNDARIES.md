# Orchestration Boundaries

This document describes how work should move through ATLAS without pretending there is already a full orchestration platform.

## Current Truth

Today, orchestration is mostly manual and session-driven:

- ATLAS provides the stack contract
- `_stack` provides current operator scripts
- Playbook provides repo-local truth in some repos
- Codex performs scoped work inside a session
- humans approve risky moves

There is no approved always-on orchestrator yet.

## Allowed Orchestration Layers

### Layer 1: Human-directed sessions

Allowed now.

Examples:

- audit the stack
- create standards
- run validators
- normalize one repo
- produce exports and receipts

### Layer 2: File-contract driven automation

Allowed now when explicit.

Examples:

- `stack.yaml`
- `AGENTS.md`
- repo-local `.codex/config.toml`
- `runtime/receipts/validation/*.json`
- export manifests

These are safe because they are inspectable and replayable.

### Layer 3: Future recommendation orchestration

Allowed later, not now.

Examples:

- CORTEX ranking next tasks
- CORTEX reading receipts and suggesting migrations
- CORTEX emitting proposed handoff manifests

These outputs must remain advisory until proven.

### Layer 4: Autonomous multi-repo mutation

Not allowed now.

Examples:

- a background agent moving files across repos
- an orchestrator rewriting stack docs and repo code without explicit scoping
- hidden task queues that mutate active repos

## Codex Usage Rules

Use Codex for:

- setup
- migration
- validation
- scoped refactors
- documentation
- bootstrap and export tooling

Do not use Codex as a hidden memory store. If the next session needs context, write it to a file that belongs in the stack.

## Handoff Pattern Between Sessions

The safe handoff unit is a file, not a chat assumption.

Preferred handoff surfaces:

- `docs/audits/*.md`
- `docs/architecture/*.md`
- `docs/ops/*.md`
- `runtime/receipts/validation/*.json`
- `packages/snapshots/*/EXPORT-MANIFEST.*`
- repo-local `docs/repo-audit.md`
- repo-local `AGENTS.md`
- repo-local `.codex/config.toml`

Each handoff should answer:

1. what changed
2. what was validated
3. what remains blocked
4. what exact next prompt should be run

## Near-Term Orchestration Contract

Use the following loop:

1. audit first
2. propose the change
3. create standards and validators
4. normalize one repo at a time
5. stop and summarize after each phase

This is the approved orchestration pattern for now.

## Future CORTEX Handoff Contract

When CORTEX is integrated, it should hand work to Codex through explicit artifacts such as:

- `runtime/state/cortex/task-queue.json`
- `runtime/receipts/cortex/*.json`
- stack-scoped handoff manifests with:
  - target repo ids
  - allowed paths
  - required validations
  - blocking conditions

These file names are illustrative only. They are not active interfaces yet.

## What Must Stay Manual

- approval of active repo moves or renames
- approval of cross-repo structural edits
- approval of secrets changes
- promotion of CORTEX from advisory to operational
- deletion of backups, installers, bundles, or legacy drops

## Tiny Useful Scaffold

The only useful scaffold to create now is stable file-contract documentation. Do not create a fake queue runner, scheduler, daemon, or orchestration database yet.
