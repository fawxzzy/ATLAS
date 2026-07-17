# ATLAS, CORTEX, Playbook, and Codex

This document defines the clean integration boundary between the stack root, the future orchestration substrate, the repo-governance layer, and the session executor.

It is intentionally interface-first. It does not create a new orchestration system.

## Purpose

Use this file to answer four questions:

1. What each component owns.
2. Which files and paths belong to each component.
3. Which component is allowed to mutate what.
4. What remains manual until the boundary is proven.

## Component Roles

| Component | Current role | Owns | Must not own |
| --- | --- | --- | --- |
| `ATLAS` | stack root and stack contract | stack map, path policy, stack docs, stack validators, export and bootstrap tooling | repo business logic, background orchestration, hidden memory |
| `Foundation` | hosted read-only portfolio surface | public stack presentation | private operator cockpit, action routing, owner truth |
| `DiscordOS` | hosted Discord API and logical writer | Vercel edge, Supabase-backed writer state, bounded GitHub Actions polling | ATLAS governance, Playbook doctrine, a second writer |
| `CORTEX` | event-triggered root-owned read-only artifacts under `runtime/cortex/**` | event schemas, query/runtime catalogs, advisory read models, on-demand supervisor logic | stack truth, a competing daemon or scheduler, direct authority to rewrite repos |
| `Playbook` | deterministic repo runtime and governance layer | repo-local context, repo validation, repo doctrine, repo-facing automation contracts | stack-wide filesystem truth, global orchestration state |
| `Lifeline` | intended local supervisor for Playbook Observer | loopback process supervision, logs, bounded restart, current-user logon restore | hosted platform, public control plane, stack doctrine |
| `Codex` | session executor | setup, migration, validation, refactors, docs, targeted edits, receipts produced during a session | hidden daemon behavior, durable system memory without an explicit file contract |

## What Belongs To Each Component

### ATLAS owns

- `stack.yaml`
- `README-STACK.md`
- `AGENTS.md` at the ATLAS root
- `docs/architecture/**`
- `docs/audits/**`
- `docs/ops/**`
- `ops/**`
- stack-level bootstrap, validation, export, and restore scripts
- path and packaging policy

ATLAS is the stack truth. If a stack-level doc conflicts with a repo convenience script, ATLAS wins.

The Atlas platform-layer doctrine itself is canonical in `repos/fawxzzy-atlas/README.md` and `repos/fawxzzy-atlas/docs/**`. This stack-root document is only the integration and boundary view; it must not become a second source of platform architecture truth.

### CORTEX owns now

- read-only runtime/query/catalog state under `runtime/cortex/**`
- portable event and observation schemas
- on-demand read-model and supervisor logic that consumes explicit worker artifacts
- future coordination logic only when it remains file-contract based

### CORTEX may eventually own

- portable event and observation schemas
- pattern extraction across validated stack receipts
- orchestration recommendations derived from real artifacts
- future queueing and coordination logic that works from explicit manifests
- optional memory and query surfaces that read retained state from `runtime/`

CORTEX is a root-owned subsystem, not an active managed child repo. `repos/cortex` may exist as adjacent historical context, but the active owner surface is `runtime/cortex/**`.

CORTEX should not become the place where stack truth is only implicit in code. Its inputs and outputs must stay file-contract based.

### Playbook owns

- repo-local governance contracts
- deterministic repo context surfaces
- repo validation and explainability
- repo-facing automation contracts that are specific to one repo
- doctrine that belongs to a repo rather than to the whole stack

Playbook is the repo truth layer, not the root filesystem registry.

### Codex owns

- carrying out setup, migration, validation, and refactor tasks
- producing audited edits
- writing reports, manifests, and receipts to explicit paths
- following stack and repo AGENTS files
- stopping when a boundary becomes ambiguous or risky

Codex is the worker, not the hidden platform.

## Boundary Rules

### ATLAS -> Playbook

ATLAS may declare:

- stack path rules
- repo ids
- export rules
- validation expectations

Playbook may consume those rules inside a repo, but it should not redefine them for the stack.

### ATLAS -> CORTEX

ATLAS may expose:

- `stack.yaml`
- stack receipts
- audits
- path policy
- repo registry and maturity status

CORTEX may read those files and make recommendations. It should not silently become a second source of truth for stack boundaries.

The active Cortex surface lives under `runtime/cortex/**`. It is not a repo-local execution surface and it must remain read-only unless a future contract explicitly expands it.

Active means the root-owned implementation/artifact surface is canonical. It
does not mean a continuously running Cortex process. Cortex refreshes after
accepted state changes or digests and must not become a competing daemon or
scheduler.

CORTEX may promote a default advisory consumer contract for `_stack`, but only as an explicit artifact-ref handoff. That does not grant automatic dispatch, execution authority, owner-truth mutation, transcript scraping, or Lifeline final receipt authority.

CORTEX may interpret explicit receipt artifacts and summarize proof posture, but Lifeline remains final receipt authority. Cortex receipt interpretation must not approve work, issue final receipts, mutate owner truth, execute work, dispatch `_stack` work, or scrape transcripts.

Rule: `_stack` may consume Cortex receipt interpretation artifacts only through explicit artifact refs. This consumption does not grant dispatch, execution, approval, final receipt, owner-truth, Lifeline-truth, or transcript authority.

### Playbook -> Codex

Playbook may provide:

- repo context
- repo validation commands
- repo-local mutation allowlists
- repo-specific agent and config files

Codex should use those surfaces when operating inside a repo.

### CORTEX -> Codex

Future CORTEX may eventually provide:

- ranked task candidates
- orchestration suggestions
- dependency-aware sequencing
- handoff manifests with explicit file scope

Codex should only consume those outputs when they are materialized in explicit files or APIs, not as implied chat memory.

## Path Classes

| Path class | Canonical paths | Owner |
| --- | --- | --- |
| stack code and tooling | `ops/**`, stack-level scripts | `ATLAS` |
| repo code | `repos/**` source trees | repo owner |
| mutable retained state | `runtime/**` | stack runtime tools |
| disposable state | `tmp/**` | current task only |
| exports and packages | `packages/**` | stack export tooling |
| durable non-secret data | `data/**` | stack data contract |
| doctrine and standards | `docs/**`, plus repo-local doctrine where repo-owned | `ATLAS` or repo owner |
| secrets | `secrets/**` | local machine operator only |

## Doctrine Split

Use this rule:

- stack doctrine lives in `docs`
- repo doctrine lives in the repo that it governs

Examples:

- stack path policy -> `docs/architecture/PATH-POLICY.md`
- stack operations -> `docs/ops/STACK-OPERATIONS.md`
- Playbook repo command truth -> `repos/fawxzzy-playbook/docs/**`
- Atlas platform architecture and contract doctrine -> `repos/fawxzzy-atlas/docs/**`

## Maturity Rule For CORTEX

CORTEX is not the active orchestration authority in ATLAS. It is currently a root-owned read-only subsystem.

It can become one only after all of the following are true:

1. its inputs are explicit and versioned
2. its outputs are file-contract based
3. its recommendations can be validated against stack receipts
4. it does not require hidden local state to reproduce decisions

Until then, CORTEX stays a read-only supervisor and query/runtime surface, not the current controller.

## Runtime Placement Boundary

The canonical component-level placement and availability contract is
`docs/registry/ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json`; the Atlas Book human
projection is `docs/atlas-book/16-runtime-placement.md`.

Current boundary:

- no new general-purpose ATLAS server
- Foundation remains the hosted read-only portfolio
- DiscordOS remains the hosted Vercel/Supabase/GitHub Actions writer runtime
- Playbook Observer is the private loopback cockpit on `127.0.0.1:4300`
- Lifeline is the intended local supervisor and logon restoration mechanism
- `_stack` has one serialized bounded scheduled sweep, not permanent pollers
- ATLAS root, Cortex, Atlas Book, contracts, registries, Socials OS, and Playbook CLI stay on demand or in owner lanes

Reconciled through 2026-07-17, Foundation and DiscordOS are hosted and operational;
the Observer foreground proof, Lifeline bounded supervision/restore proof, and
one `_stack` scheduled-sweep proof are accepted from merged owner evidence.
Current Observer state is intentionally stopped/restorable and the Lifeline and
`_stack` tasks are ready. One accepted activation event refreshed the principal
Cortex `latest` read models from pinned source-only authority; unavailable owner
and runtime health remains unknown. Actual later new-logon restoration and
sustained unattended uptime are unknown. Accepted proof is not converted into a
claim of current running uptime.

Activation steps carry structured `accepted`, `pending`, `blocked`, or
`unknown` status plus evidence. The selector is derived as the first
non-accepted step in the frozen sequence. Cortex step 6 is accepted and the
selector now names `DiscordOS interaction-first reliability review` as step 7.

## Safe Integration Pattern

Use this order:

1. ATLAS defines the contract
2. Playbook validates repo-local behavior
3. Codex executes scoped changes against the contract
4. receipts are written to `runtime/receipts/**`
5. CORTEX reads receipts and worker artifacts, then recommends the next step or emits a merge request

That preserves human review and keeps orchestration explainable.

## What Stays Manual For Now

- deciding whether CORTEX is promoted from framework to active stack service
- approving broad cross-repo refactors
- changing secrets handling
- moving active repos
- promoting recommendations into automatic orchestration
- any queue runner that can mutate multiple repos without review
