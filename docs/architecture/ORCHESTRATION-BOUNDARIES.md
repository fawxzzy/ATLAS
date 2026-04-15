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

Awareness is no longer the primary missing layer. ATLAS already has registry-backed truth, typed runtime observations, working memory, and a query-first awareness surface. The missing layer is governed initiative management above sessions.

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
- a root initiative loop clustering attention, plans, decisions, hypotheses, and recent sessions into initiatives
- CORTEX or root-owned tooling emitting proposed handoff manifests or proposed sessions

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

1. awareness
2. attention
3. initiative
4. proposed session
5. approval
6. execution
7. receipt
8. memory refinement

For the current stack posture, only the later stages are approved for execution:

- initiative and proposed-session outputs remain advisory
- execution still requires the governed session path
- receipts and memory refinement must be file-contract based
- nothing may bypass approval by pretending a proposal is execution authority

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

The only useful scaffold to create now is stable file-contract documentation and advisory initiative artifacts. Do not create a fake queue runner, scheduler, daemon, or orchestration database yet.
