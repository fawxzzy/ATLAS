# Awareness-First World Model

This document turns the awareness-first requirement into stack-owned contracts for ATLAS.

It is a stack boundary document, not a replacement for platform doctrine in `repos/fawxzzy-atlas/docs/**`.

## Purpose

ATLAS should not aim for "every component knows everything."

ATLAS should aim for this stricter invariant:

**Not everything knows everything. Nothing meaningful stays dark. Nothing meaningful stays unowned.**

**No dark state:** any state that can change behavior must be represented as at least one of:

- a registered surface
- a typed artifact
- an append-only observation or receipt
- a deterministic snapshot or attention view derived from the above

If behavior depends on state that exists only in one process memory, one terminal scrollback, or one person's recollection, the system is not awareness-first yet.

Client rule:

- ATLAS is the source of truth
- chat, voice, CLI, dashboards, and hosted connectors are clients
- clients query awareness first and hydrate narrower artifacts second

## World-Model Layers

| Layer | Question answered | Current ATLAS surface | Required rule |
| --- | --- | --- | --- |
| registry | what may exist or be invoked | `docs/registry/**`, `schemas/atlas.tool.catalog.entry.v1.json`, `schemas/atlas.extension.manifest.v1.json` | unknown surfaces fail closed |
| artifact | what durable object exists | `schemas/atlas.artifact.descriptor.v1.json`, `runtime/cortex/artifacts/**` | important objects have typed identity and digest |
| observation | what happened | `runtime/receipts/**`, `runtime/lifeline/worker-execution/**`, `runtime/receipts/events/**`, knowledge receipts | actions and decisions are receipt-backed, not transcript-backed |
| snapshot | what is true now | `ops/cortex/render_status.py`, `runtime/atlas/sessions/*/status.snapshot.json`, `runtime/cortex/query/knowledge/bundle.json` | current truth is derived from explicit artifacts only |
| attention | what requires a choice | status `attention_queue`, future queue-like read models under `runtime/state/**` when needed | anomalies are first-class outputs, not hidden interpretation |

## Current Mapping

ATLAS already has most of the substrate required for awareness-first behavior:

- pinned stack truth through `stack.lock.yaml`
- registry-backed governed tool surfaces
- content-addressed artifact descriptors
- typed session manifests, worker assignments, worker status artifacts, and execution receipts
- a query-first awareness layer through status, the Awareness API, voice, MCP, and read-model artifacts
- a typed world model with explicit snapshot and attention outputs
- structured working memory for plans, decisions, initiatives, and hypotheses
- stable platform-boundary contracts instead of repo folklore
- explicit privilege requests, approvals, and execution receipts

The global index layer is therefore partially implemented already as registry + descriptors + observations + snapshot + attention + working memory + Awareness API.

That means the main missing layer is no longer basic awareness. The next gap is initiative management above sessions, durable proposal and portfolio handling, durable extension lifecycle, and governed action progression on top of the current awareness substrate.

That initiative layer is now represented explicitly by:

- initiative artifacts under `docs/memory/initiatives/**`
- non-executing proposed sessions under `runtime/atlas/proposed-sessions/**`
- proposal provenance that binds attention, supporting evidence, and prior governed work together

Conversation now sits above that substrate as a governed client runtime:

- conversation manifests under `runtime/atlas/conversations/**`
- grounded turn artifacts with deterministic retrieved refs and provenance
- proposal-only follow-up authored from explicit refs instead of hidden chat state

## Operating Loop

The root operating loop is:

1. awareness
2. attention
3. initiative
4. proposed session
5. approval
6. execution
7. receipt
8. memory refinement

Current ATLAS can already:

- see itself through the world model, status, and awareness surfaces
- remember in structured form through working memory and promoted knowledge
- expose state to chat, voice, and MCP clients
- run governed sessions
- resume paused governed work
- perform a first bounded truthful write

What it does not yet do is manage a portfolio of work over time the way an operating environment should.

Conversation now fits the operating loop like this:

- clients do not carry durable state in prompt history
- each turn queries awareness, memory, and related portfolio surfaces
- durable truth is the structured turn artifact, not the raw transcript
- action-seeking turns author proposal artifacts and memory refinements instead of executing

Initiatives therefore belong above sessions, not beside them:

- attention identifies what needs choice
- initiatives cluster repeated related work into one durable identity
- proposed sessions are advisory `request_action` outputs, not autonomous execution
- proposed sessions are indexed and fetchable, but they remain non-executing until a governed session is created
- execution still flows through the governed session path
- memory refinement updates working memory and read models from explicit evidence

If attention persists over time, it should become an initiative or be explicitly dismissed.

## Memory Contract

ATLAS should treat memory as two different classes with different rules.

### Event Memory

Event memory answers "what happened."

Use:

- `runtime/receipts/events/**`
- `runtime/receipts/knowledge/**`
- `runtime/lifeline/worker-execution/**`
- other append-only receipt lanes

Rules:

- raw receipts are immutable once written
- corrective understanding is added through new receipts or derived artifacts, not by silently rewriting history
- retention may archive timestamped duplicates only when a stable `latest.json` or equivalent compatibility target exists

### Document Memory

Document memory answers "what is known, planned, decided, or standardized."

Use:

- `docs/architecture/**`
- `docs/standards/**`
- `docs/ops/**`
- `docs/memory/**`
- `docs/knowledge/promotions/**`
- repo-owned doctrine inside the repo that owns it

Rules:

- documents are editable and reviewable
- documents must cite their explicit source files or receipt lanes when they summarize runtime truth
- document updates must not pretend to be raw event history
- structured working memory must use typed contracts for plans, decisions, initiatives, and hypotheses
- transcript residue is not memory

## Compaction Rule

Compaction is allowed only when provenance remains inspectable.

Safe compaction means:

- keep raw event or receipt lanes as the auditable source
- create summary, catalog, or query artifacts that link back to source refs and digests
- make compaction itself observable through receipts or reports

Unsafe compaction means:

- replacing the only copy of history with a summary
- rewriting state without a source ref
- carrying critical memory only in a model context window

## Attention Rule

A snapshot is not sufficient if it only lists inventory.

ATLAS should also emit an explicit attention view for operator-relevant anomalies, such as:

- blocked or paused workers
- sessions waiting for resume or merge handling
- registry load failure or registry drift
- governed surfaces that are unknown to the current registry
- failed or missing closure receipts
- quarantined trust surfaces that still require review or containment

Attention is a read model. It does not grant execution authority.

## Governed Artifact Epochs

ATLAS uses an explicit governed-artifact epoch boundary for historical runtime truth.

Registry-backed governed artifacts cut over on **2026-04-14T08:06:53Z**.

Epoch classes:

- `legacy_pre_registry`: artifacts that predate the cutover and cannot truthfully satisfy the governed_v1 identity or closure contract
- `governed_v1`: artifacts created at or after the cutover, or older artifacts that already carry the governed identity and closure contract

Epoch behavior:

- `governed_v1` stays fail-closed for governed identity, required observations, and closure evidence
- `legacy_pre_registry` stays visible in the world model, awareness, and status surfaces
- `legacy_pre_registry` is non-blocking for impossible modern fields, but it must emit an explicit compatibility signal until it is backfilled or archived
- original historical artifacts are not rewritten in place just to fake governed identity

## World-Model Artifact Paths

Current root-owned outputs:

- global state snapshot: `runtime/state/atlas/world-model.snapshot.latest.json`
- global attention snapshot: `runtime/state/atlas/world-model.attention.latest.json`
- session-local status snapshot: `runtime/atlas/sessions/<session_id>/status.snapshot.json`

Current machine-readable contracts:

- `schemas/atlas.observation.v1.json`
- `schemas/atlas.inventory.entry.v1.json`
- `schemas/atlas.attention.item.v1.json`
- `schemas/atlas.state.snapshot.v1.json`
- `schemas/atlas.plan.v1.json`
- `schemas/atlas.decision.v1.json`
- `schemas/atlas.initiative.v1.json`
- `schemas/atlas.hypothesis.v1.json`

## Enforceable Rule

`No dark state` is not doctrine only.

At the stack root it means:

- completed governed sessions must appear in the world-model inventory and observation surfaces
- governed execution receipts must produce matching observations
- attention is derived from explicit observations and descriptors, not operator memory
- world-model snapshots must be rebuildable and content-digest stable from the same inputs
- durable plans and decisions must live in structured working-memory artifacts rather than transcript-only summaries

If those artifacts are missing, the stack is out of contract.

## Completed Governed Flow Contract

A governed flow is complete only when the required artifacts, receipts, and observations all exist and agree.

Required artifact set for a completed governed flow:

- `runtime/atlas/sessions/<session_id>/session.manifest.json`
- `worker.assignment.json`
- `worker.status.running.json`
- `privileged-action.request.json`
- `approval.receipt.json`
- `runtime/lifeline/worker-execution/<assignment_id>/receipt.json`
- `worker.status.completed.json`
- closure evidence in `completion.close_receipt_refs`

Required observation matrix:

| Owner | Observation | Required when |
| --- | --- | --- |
| `_stack` | `assignment_created` | governed assignment exists |
| `_stack` | `heartbeat` | governed worker enters running state |
| Lifeline | `execution_requested` | governed execution request exists |
| Lifeline | `execution_approved` / `execution_rejected` / `execution_expired` | approval receipt exists |
| Lifeline | `execution_completed` | execution receipt exists |
| `_stack` | `completed` | final worker state is `completed` or `failed` |
| `_stack` | `merge_requested` | supervisor emitted merge request |
| `_stack` | `paused` | worker paused for merge |
| `_stack` | `merger_assigned` | merger worker assignment exists |
| `_stack` | `resume_ready` | resume context or merge completion exists |

Every governed observation must carry:

- `session_id`
- `worker_id` when applicable
- `assignment_id` when applicable
- `stack_lock_digest`
- `tool_id`
- `extension_id` when applicable
- `registry_digest`
- `source_artifact_refs`

Root is the publication destination and state builder. `_stack` and Lifeline emit facts; they do not become alternate session stores.

Historical exception rule:

- a `legacy_pre_registry` session may be incomplete
- a `legacy_pre_registry` session may not be invisible
- compatibility status for legacy history must be explicit in the attention layer

## Working-Memory Guardrails

Working memory is structured memory, not transcript dumping.

Required behavior:

- plans, decisions, initiatives, and hypotheses stay in typed artifacts under `docs/memory/**`
- each item stays small, linked, and superseding rather than acting as a second knowledge junk drawer
- runtime catalog output at `runtime/cortex/catalog/memory/working-memory.latest.json` must be rebuildable from those source documents
- working-memory artifacts must carry stable digests and provenance fields so world-model snapshots can cite them directly
- deterministic authoring tools may create or update working-memory items from governed session closure evidence, but they must stay transcript-free and idempotent

Conversation-specific rule:

- raw chat transcript and raw audio are excluded from the durable memory lane
- only turn summaries, refs, provenance, and separately authored memory updates count as durable truth

Boundary rule:

- knowledge docs are durable promoted truth
- working memory is active reasoning scaffold and decision record
- observations and receipts are hot operational truth

When those lanes blur, awareness quality degrades even if all of the files still exist.

## Connector Boundary

Any external chat, voice, or app connector must bind to the same governed model:

- discoverable surfaces come from the registry, not ad hoc prompts
- reads consume snapshots, catalogs, and descriptors where possible
- clients should query first, then hydrate narrower artifacts only when needed
- writes or execution requests flow through Lifeline or another approved executor
- privileged actions still require approval and receipts

Conversation-client rule:

- a conversation client may keep a local transcript for UX, but not as system truth
- durable conversation state must stay reconstructable from the stored manifest and turn artifacts
- the automation ceiling for conversation clients is proposal-only: `request_action`

An external client may be a better interface, but it must not become a second execution or memory authority.

## Before Wave 7

Before expanding orchestration, ATLAS should keep these invariants hard:

1. no decision-relevant state lives only in transcripts, logs, or RAM
2. all governed surfaces are registry-backed and fail closed when unknown
3. status remains descriptor-driven rather than terminal-driven
4. attention items are derived explicitly from typed artifacts
5. memory refinement preserves source refs and digests

## Non-Goals

- no background daemon that mutates repos without scoped artifacts
- no hidden cross-repo queue runner
- no "smart memory" that silently edits doctrine or repo code
- no promotion of Cortex from advisory to executor without a separate contract
