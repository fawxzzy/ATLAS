# ATLAS Engineering Memory Enforcement

Status: installed end to end in every currently admitted engineering source-mutation executor

Date: 2026-08-21

## Objective

Turn the question “have we solved this before?” into a required engineering
gate. The user may continue supplying rough natural-language notes. ATLAS and
Codex own normalization, precedent search, scope control, proof, and archival.

The enforced flow is:

```text
rough note
  -> canonical card + job identity
  -> engineering-memory profile
  -> precedent search
  -> mutation gate
  -> smallest coherent change
  -> verification gate
  -> completion archive
  -> archive gate + execution receipt + card reconciliation
```

## Existing Conventions Found

- `atlas.job-envelope.v2` and `atlas.execution-receipt.v2` are the canonical
  task/result seam.
- `atlas.card-record.v2` and `atlas.board-event.v2` are the canonical queue and
  board projection seam.
- `atlas.knowledge-candidate.v2` already carries evidence-backed Rule, Pattern,
  and Failure Mode candidates into reviewed promotion.
- `docs/architecture/VISUAL-CHANGE-WORKFLOW.md` already requires a canonical
  surface, a pre-mutation checklist, route-aware screenshots, and itemized
  reconciliation.
- `docs/registry/ATLAS-UI-STANDARDS-REGISTRY.v1.json` already defines
  deterministic UI evidence, canonical component ownership, and fail-closed
  visual gates.
- `ops/atlas/build_codex_context.py` already builds governed Codex context and
  can query the knowledge plane.
- `ops/atlas/native_task_lifecycle.mjs` already blocks archival without a
  durable receipt.

## Missing Convention and Root Cause

The primitives existed but were not joined at the implementation boundary.
Normal Codex context packs queried knowledge only when the task intent itself
was `knowledge`. Ordinary implementation, governance, and operator tasks could
therefore reach source work without an indexed precedent pass. No gate required
the current repository search, reuse decision, UI parity contract, or visual
evidence to be attached to the canonical task identity.

This is the enforcement gap. Creating another queue or another Playbook would
make it worse.

## Integration Point

The additive `atlas.engineering-memory-profile.v1` object lives at:

```text
atlas.job-envelope.v2.extensions.engineering_memory
```

It is correlated to the existing canonical card through
`job.correlations.card_id`. The profile is not a second task record. It carries
the detailed engineering phase and the evidence required to pass lifecycle
gates for the same job/card identity.

Canonical references:

- policy: `docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json`
- producer inventory: `docs/registry/ATLAS-ENGINEERING-MEMORY-PRODUCER-INVENTORY.v1.json`
- profile schema: `packages/atlas-contracts/schemas/atlas.engineering-memory-profile.v1.schema.json`
- closeout schema: `packages/atlas-contracts/schemas/atlas.engineering-memory-closeout.v1.schema.json`
- runner-verification schema: `packages/atlas-contracts/schemas/atlas.engineering-memory-runner-verification.v1.schema.json`
- gate: `ops/atlas/engineering_memory_gate.mjs`
- terminal reconciler: `ops/atlas/complete_engineering_memory_job.mjs`
- reusable prompt: `docs/prompts/atlas-workflow/atlas.engineering-memory.md`
- seeded knowledge: `docs/knowledge/patterns/engineering-memory-enforcement.md`

## Single Source of Truth Task Model

| Concern | Canonical source |
|---|---|
| Queue identity, owner, priority, board status | `atlas.card-record.v2` |
| Bounded objective, scope, runtime, authority, verification | `atlas.job-envelope.v2` |
| Engineering-memory phase and evidence | `job.extensions.engineering_memory` |
| Applied board transition and readback | `atlas.board-event.v2` |
| Terminal execution result | `atlas.execution-receipt.v2` |
| Reusable learning candidate | `atlas.knowledge-candidate.v2` |

The gate rejects a missing card ID, mismatched task/card/project/repository
identity, and phase/card lifecycle drift.

Engineering phases map to the existing card lifecycle instead of replacing it:

| Engineering phase | Allowed card lifecycle |
|---|---|
| `captured` | `intake` |
| `normalized` | `intake`, `planning` |
| `precedent_checked`, `planned` | `planning`, `ready` |
| `in_progress` | `in-progress` |
| `implemented` | `in-progress`, `review` |
| `verified` | `review`, `completed` |
| `archived` | `completed`, `archived` |
| `blocked` | `blocked` |
| `reopened` | `planning`, `ready`, `in-progress` |

## Natural-Language Intake

The user supplies the original note. Atlas/Codex writes the structured profile;
the user does not fill a template.

Required normalized fields include:

- original source text and normalized title;
- stable task ID, project, repository, routes/states, and components;
- task type and acceptance criteria;
- precedent queries, searched sources, matches, and reuse decision;
- technical and visual verification requirements;
- parent scope lock and linked child IDs;
- fast/normal lane classification;
- archive state and blockers.

Parity phrases such as `same as`, `match`, `carry over`, `make it like`,
`reuse`, and `same component` are classified as `ui_parity`. The gate rejects
generic visual classification when the source note contains those parity cues.

## Precedent Lookup Contract

Before mutation, search at least:

1. the current repository;
2. ATLAS docs and registries.

Search Playbook, sibling repositories, task archives, design-system docs, tests,
and visual fixtures when the task makes them relevant. Each search records:

- source kind and exact reference;
- `match`, `no_match`, or `unavailable`;
- evidence references;
- direct, adaptable, or rejected matches;
- final decision: `reuse`, `adapt`, `reject`, or `first-durable-pattern`;
- rationale and check timestamp.

If nothing matches, record:

```text
No matching precedent found. Creating first durable pattern.
```

If a match is rejected, explain why copying or centralizing it would be wrong.

## Gates

Validate normalized planning evidence:

```powershell
node ops/atlas/engineering_memory_gate.mjs `
  --job-envelope <job.json> `
  --card-record <card.json> `
  --gate plan
```

Before the first source change:

```powershell
node ops/atlas/engineering_memory_gate.mjs `
  --job-envelope <job.json> `
  --card-record <card.json> `
  --gate mutation `
  --output runtime/atlas/engineering-memory-gates/<task-id>.mutation.json
```

Before `verified`, run the same command with `--gate verify`. Before archival,
create the repo-visible completion record and run it with `--gate archive`.
Installed executors do not trust the worker to advance those terminal states
directly. The worker writes one schema-valid closeout record; the runner writes
its own verification record; and the Atlas-root terminal reconciler merges the
evidence, advances the existing JobEnvelope/CardRecord, and emits both receipts.

The mutation gate requires:

- canonical card correlation and consistent identities;
- a mutable workspace and a ready/in-progress card;
- frozen parent acceptance criteria;
- usable current-repo and ATLAS-doc searches;
- a final precedent decision;
- parity and fast-lane contracts when applicable.

The verify gate requires passed evidence. The runner, not the worker summary,
owns technical command exit status. Visual tasks additionally require worker-
supplied passed screenshot, DOM, or visual-diff evidence covering the canonical
source and every target surface. The archive gate verifies that a mutating task's
completion record exists under the bound workspace `docs/`. A verified no-change
run may use only its generated closeout under `.codex/logs/`; this exception does
not admit a source mutation or a substitute docs archive.

Directly bypassing this supported entrypoint is a policy violation. The shared
`_stack` repo-task and canonical-workspace producers now invoke it before Codex
starts and reconcile it again before terminal success. The current producer
inventory proves that all higher-level engineering entrypoints delegate to one
of those executors. A future direct source-mutation launcher is uninstalled by
definition until it proves the same mutation, verify, and archive chain in CI.

## Shared Producer Installation

`repos/_stack/ops/codex/AtlasContractsV2Producer.ps1` installs the policy at the
existing execution seam. For both shared execution classes it now:

1. retains the rough prompt as a run artifact;
2. calls `ops/atlas/prepare_engineering_memory_job.mjs`;
3. derives one stable card identity and `atlas.card-record.v2` projection;
4. attaches the normalized profile to the existing JobEnvelope;
5. searches the exact target workspace and Atlas docs;
6. validates the updated job, card, and existing execution contracts;
7. requires a passed mutation-gate receipt before Codex invocation;
8. supplies the exact source, card, search, and gate paths to the worker;
9. requires a schema-valid closeout record from a mutating worker;
10. records runner-owned technical verification or validated no-change proof;
11. invokes `ops/atlas/complete_engineering_memory_job.mjs` before commit or
    terminal success;
12. requires passed verify and archive receipts and an archived JobEnvelope/Card;
13. carries the complete artifact chain into the terminal ExecutionReceipt.

The installed producer defaults rough notes to the normal lane. It does not
infer fast-lane authority, external effects, production authority, or a visual
completion claim. Workers provide route-aware visual/manual evidence and the
repo-visible closeout; the runner independently owns technical verification and
is the only component that can reconcile the terminal phases.

The `_stack` authoritative verification path and its versioned GitHub Actions
fixture now contain the root-owned normalizer, terminal reconciler, gates,
schemas, and semantic validators. The integration fixture proves:

```text
prompt trigger
  -> normalized JobEnvelope + CardRecord
  -> precedent search
  -> passed mutation gate
  -> fake Codex execution
  -> runner-owned verification
  -> worker closeout + repository docs archive
  -> passed verify and archive gates
  -> archived JobEnvelope + CardRecord
  -> terminal ExecutionReceipt
  -> accepted prompt archive
```

## UI Parity Enforcement

A parity profile names:

- canonical source surface;
- all target surfaces;
- shared properties such as color, shape, animation, container, spacing, and
  behavior;
- one implementation strategy: shared component, shared style contract, or
  documented variant;
- screenshot/DOM/visual-diff evidence for source and all targets.

Independent divergent implementations are not accepted silently. Either
centralize the semantic control, share its style/token contract, or document why
the variant is intentional.

## Visual Verification Loop

Reuse `docs/architecture/VISUAL-CHANGE-WORKFLOW.md` and the owner repository's
QA contract. The engineering-memory layer adds the lifecycle rule:

1. bind the route/state and expected surface before mutation;
2. capture before evidence when reproducible;
3. implement from the canonical component or pattern;
4. capture after evidence on every affected state;
5. reconcile each acceptance item;
6. retain missing proof as `unverified` and stop short of `verified`.

Hard-to-reach states should use an existing fixture route, state loader, QA flag,
or deterministic seed. Adding a new harness is a child task when it exceeds the
parent's frozen acceptance criteria.

## Five-Minute Patch Lane

`fast` is a bounded workflow label, not a timing promise. It is allowed only
when:

- one clear issue affects one or two components;
- the verification route is known;
- acceptance criteria are simple;
- no schema, migration, Auth, security, production, secret, billing, or
  destructive boundary is involved;
- no disqualifier remains.

Its receipt sequence is:

```text
Captured -> Precedent checked -> Changed -> Verified -> Archived
```

If scope or proof expands, switch the profile to `normal`; do not hide the
expansion to preserve a fast-lane label.

## Expansion Control

Freeze the parent's acceptance criteria before mutation. A discovered issue is
either necessary to meet those criteria or it becomes a linked child task with
its own stable ID, status, and acceptance criteria. Silent absorption is
forbidden. This keeps one growing task from erasing the rest of the queue.

## Knowledge Capture

Closeout can still emit `atlas.knowledge-candidate.v2`. The seeded ATLAS-root
entries are:

- Rule: Precedent Lookup Before Implementation
- Rule: Visual Work Requires Visual Evidence
- Rule: Do Not Fragment Task State
- Pattern: Shared Semantic Control
- Pattern: PWA Standalone Safe-Area Layout
- Failure Mode: Claimed Carryover Without Parity
- Failure Mode: Expanding Task Erases Queue
- Decision: Atlas Is Enforcement, Not Memory Alone

They are accepted for ATLAS workflow enforcement. Playbook promotion remains a
reviewed candidate boundary; this task does not overwrite Playbook doctrine.

## Dry Run 1: Mazer Settings-Control Parity

Fixture pair:

- `packages/atlas-contracts/fixtures/examples/engineering-memory/mazer-settings-parity.card-record.v2.json`
- `packages/atlas-contracts/fixtures/examples/engineering-memory/mazer-settings-parity.job-envelope.v2.json`

Classification:

| Field | Result |
|---|---|
| Rough note | “The gameplay settings icon still does not match the main menu one.” |
| Task type | `ui_parity` |
| Source/target | reported menu settings control -> reported play settings control |
| Shared properties | color, shape, animation, container, spacing, behavior |
| Current repo search | match found, but rejected as the claimed pair |
| Current source evidence | `MenuScene.ts` centralizes menu/play, exposes menu Options, and routes play through Pause |
| Decision | reject stale identity and block mutation pending current visual reproduction |
| Verification | capture current menu and play/Pause states at the same viewport |
| Archive outcome | no completion archive; task remains `blocked` with the exact identity-drift reason |

This is deliberate. Engineering memory must prevent a stale historical
description from causing a fabricated “parity fix” against current source.

## Dry Run 2: Fitness Standalone Bottom Layout

Fixture pair:

- `packages/atlas-contracts/fixtures/examples/engineering-memory/fitness-pwa-bottom-layout.card-record.v2.json`
- `packages/atlas-contracts/fixtures/examples/engineering-memory/fitness-pwa-bottom-layout.job-envelope.v2.json`

Classification:

| Field | Result |
|---|---|
| Rough note | installed app should reach the bottom without reserving browser-toolbar space |
| Task type | `pwa_layout` |
| Routes/states | `/today` browser and standalone |
| Current precedent | `AppShell.tsx`, `PersistentAppChrome.tsx`, `globals.css`, `mobile-shell-contract.md` |
| Decision | reuse the shared shell/display-mode/safe-area contract |
| Implementation guidance | fix or reuse the shell owner; do not add route-local bottom padding |
| Verification | equivalent mobile captures in browser and standalone plus repo-local checks; physical proof remains explicit |
| Archive outcome | not yet eligible; the dry run remains `planned` with visual evidence listed as unverified |

The dry run proves the precedent is discoverable while refusing to claim that a
new app change was implemented or visually verified.

## Verification Surface

Focused verification for this contract is:

```powershell
node --test tests/test_atlas_engineering_memory_gate.mjs
node --test tests/test_atlas_engineering_memory_intake.mjs
node --test tests/test_atlas_engineering_memory_closeout.mjs
node --test tests/test_atlas_engineering_memory_producer_inventory.mjs
python -m unittest tests.test_atlas_codex_context
npm --prefix packages/atlas-contracts run validate
powershell -NoProfile -ExecutionPolicy Bypass -File repos/_stack/ops/codex/Test-AtlasContractsV2Producer.ps1
pnpm --dir repos/_stack run codex:stack:verify
```

The Mazer and Fitness repositories are read-only evidence sources in this task.
No owner source, provider, live data, deployment, or production mutation is
authorized or claimed.
