# Atlas Creation OS Target Architecture

- Status: **RECONCILED TARGET**
- Date: 2026-07-16
- Research basis: [governed external import](../../data/imports/creation-os/deep-research-2026-07-16/IMPORT-MANIFEST.json)
- Reconciliation: [Creation OS research decision report](../audits/ATLAS-CREATION-OS-RESEARCH-RECONCILIATION-2026-07-16.md)

## Product definition

**RECONCILED TARGET** - Atlas is a human-directed creation operating system
that turns intent into governed, verifiable software and artifacts while
preserving durable context, explicit ownership, and final human authority.

## Phase-one wedge

**RECONCILED TARGET** - The first product wedge is a voice-capable software,
app, and tool builder with:

- repository ingestion and compatibility analysis;
- governed, bounded execution in explicit workspaces;
- deterministic tests, diffs, and previews;
- durable memory and task context with provenance;
- reversible side effects and explicit approvals;
- human acceptance before external or production mutation.

Voice is a high-value interaction surface, not a separate authority system.
The deterministic builder loop remains the path from intent to accepted change.

## Phase-one non-goals

**REJECTED/NOT ADOPTED NOW**:

- a monolithic AGI or one agent that owns every system;
- training a custom foundation model;
- replacing proven ChatGPT or Codex transport before replacement parity exists;
- deploying a new general-purpose Atlas server;
- selecting or deploying PostgreSQL, Qdrant, Neo4j, Redis, MinIO, Temporal,
  LangGraph, LiveKit, OPA, Cosign, or equivalent infrastructure merely because
  it appears in external research;
- building XR, robotics, device control, game-engine, and enterprise-scale
  surfaces in parallel with the first wedge;
- storing all memory in one file or in one model context window;
- automatic production deployment, external mutation, purchasing, or physical
  actuation;
- moving owner-repository implementation truth into Atlas root.

## Current truth and target ownership

The target composes the current stack instead of inventing a replacement
monolith.

| Layer | Current or target role | Authority boundary |
| --- | --- | --- |
| Atlas kernel and governance | **VERIFIED CURRENT ATLAS** - root topology, path policy, source hierarchy, contracts, approvals, markers, accepted receipts, and cross-repo consequence | Does not own product implementation or infer external authority |
| Playbook doctrine and profiles | **VERIFIED CURRENT ATLAS** - reusable rules, patterns, failure modes, repo profiles, verification, and review semantics | Doctrine promotion remains owner-reviewed; research is not doctrine |
| Atlas Contracts interoperability | **VERIFIED CURRENT ATLAS** - versioned identity, job, context, lease, evidence, receipt, board, marker, knowledge-candidate, and approval semantics | Shared meanings stay Atlas-owned; owner extensions do not redefine them |
| Cortex intelligence and context | **VERIFIED CURRENT ATLAS** - root-owned advisory context, routing, synthesis, replay, and read models | No scheduling, owner mutation, deployment, board write, or final approval authority |
| `_stack` execution | **VERIFIED CURRENT ATLAS** - governed workspace/action routing, operator commands, event normalization, and deploy entrypoints | Execution capability does not create production approval or product truth |
| DiscordOS coordination | **VERIFIED CURRENT ATLAS** - one logical board, publication, and readback writer | Does not infer Git, test, deploy, or product truth from prose |
| Owner repositories and domain planes | **VERIFIED CURRENT ATLAS** - product, code, runtime, release, and domain truth | Each owner remains authoritative for its implementation and proof |
| Creation OS product surface | **RECONCILED TARGET** - composes the layers above into one builder and creative experience | Must preserve every existing authority boundary and acceptance gate |

Lifeline, Foundation, Playbook, Cortex, `_stack`, DiscordOS, Atlas root, Atlas
Contracts, Atlas Control, and the Atlas Book remain distinct systems inside the
later post-preparation development program. Fitness, Mazer, and Socials OS
remain separate owner lanes; reusable contracts and evidence may converge, but
their product implementation does not.

## Planner and PM role

**RECONCILED TARGET** - "planner/PM" is a governed role across existing Atlas
surfaces, not a new all-owning agent:

- the human operator and ATLAS MAIN own intent, priority, acceptance, and final
  direction;
- Cortex may assemble context, decompose work, compare options, and recommend a
  plan;
- Atlas root applies topology, contract, policy, approval, marker, and receipt
  rules;
- `_stack` admits and executes bounded jobs through current action contracts;
- owner repositories validate product/code truth and accept owner-side change;
- DiscordOS projects authorized board or publication consequences through one
  logical writer.

The role may coordinate specialists, but cannot become a competing source of
truth, hidden scheduler, automatic dispatcher, or external-mutation authority.

## Core platform, surfaces, and verticals

**RECONCILED TARGET**:

- Core platform: identity, contracts, context, memory tiers, governed
  execution, policy, approvals, evidence, receipts, observability, recovery,
  and owner adapters.
- Surfaces: software builder, repository migration, voice conversation,
  blueprint visualization, and later device interaction.
- Verticals: domain-specific products and workflows built on the core through
  explicit contracts, including separate owner products.

Platform contracts must remain usable without any one surface. A surface must
not redefine shared identity, evidence, or authority. A vertical owns its
domain behavior and may extend contracts through namespaced fields, but cannot
silently change core meanings. New surfaces and verticals receive independent
admission, measurement, migration, and rollback paths.

## Interaction loops

### Deterministic builder loop

**RECONCILED TARGET**:

```text
human goal
-> explicit product/spec contract
-> repository and dependency ingestion
-> compatibility and risk plan
-> bounded workspace and authority envelope
-> proposed diff and generated artifacts
-> tests, static checks, and preview
-> evidence bundle and execution receipt
-> human review and acceptance
-> separately authorized merge, deploy, publication, or other side effect
```

Required properties:

- deterministic identities from goal through receipt;
- literal changed-path and verification scope;
- fail-closed behavior when source, authority, or proof is missing;
- no direct transition from conversational intent to production mutation;
- rollback or recovery contract for every non-trivial side effect;
- artifact hashes and provenance preserved through handoff.

### Conversational and creative loop

**RECONCILED TARGET**:

```text
voice or text exploration
-> Cortex-assisted context and options
-> conversational branch, mockup, or preview
-> user refinement and comparison
-> explicit candidate selection
-> deterministic builder-loop admission
```

The creative loop optimizes latency, interruption, exploration, and rapid
preview iteration. It may produce proposals and disposable branches. It does
not bypass policy, tests, receipts, owner truth, or human approval. A chained,
transcriptable path is preferred when a task approaches sensitive mutation;
the exact realtime transport remains a **DEFERRED DECISION**.

## Source-of-truth and evidence hierarchy

**VERIFIED CURRENT ATLAS** - The Creation OS inherits the accepted Atlas order:

1. Current executable/local owner evidence and authenticated timestamped
   read-only external responses for their respective planes.
2. `stack.yaml` for declared topology and policy, with lock or inventory drift
   kept explicit.
3. Current validation receipts for health.
4. Atlas Book marker surfaces only when backed by accepted receipts and
   continuity manifests.
5. Continuity and restart indexes as projections, never implementation proof.
6. Current owner-repository evidence for owner product and code truth.
7. Chats, delegations, and handoffs as intent and routing evidence only.
8. Historical, archived, and external research documents as provenance only.

No lower source overwrites a higher source because it is newer-looking,
persuasive, or marked complete.

## Bootstrap manifest contract

**RECONCILED TARGET** - Atlas will use a signed, versioned bootstrap manifest
as a minimal recovery pointer into governed truth. The manifest is not the
memory system.

Minimum semantic fields:

- manifest contract ID and semantic version;
- manifest instance ID and monotonic revision;
- subject identity and workspace references, not duplicated profile bodies;
- source-hierarchy root references;
- policy and approval-policy references;
- component, contract, and owner-registry references;
- retained state, receipt, catalog, and recovery-checkpoint references;
- referenced-artifact digests or integrity metadata;
- signer identity or key fingerprint and detached signature reference;
- creation/update timestamps and previous-version or recovery-chain reference.

The manifest must not contain:

- all conversations, memories, documents, embeddings, graphs, or artifacts;
- secret values, private signing keys, provider credentials, or raw tokens;
- copied owner-repository truth;
- mutable queue state without an authoritative external reference;
- a required vendor-specific backend contract;
- authority to execute, deploy, publish, purchase, or actuate.

Recovery behavior:

1. Verify schema version, signature, signer trust, and manifest digest.
2. Resolve source hierarchy and policy before mutable state.
3. Resolve owner and contract registries.
4. Verify referenced artifact digests and freshness independently.
5. Rebuild derived indexes and Cortex read models from governed sources.
6. Stop with an explicit unknown or degraded state when any required pointer
   is unavailable or contradictory.

Implementation format, signing mechanism, key custody, revocation, rotation,
storage location, replication, and disaster-recovery procedure remain
**DEFERRED DECISION** items in the
[bootstrap ADR candidate](../atlas/decisions/adr-signed-versioned-atlas-bootstrap-manifest.md).

## Memory tiers and boundaries

**VERIFIED CURRENT ATLAS** supplies the current placement contract;
**RECONCILED TARGET** adds explicit retrieval and compaction semantics without
selecting a backend.

| Tier | Canonical role | Examples | Compaction rule |
| --- | --- | --- | --- |
| T0 source authority | Versioned governance and owner truth | Git, `stack.yaml`, owner-repo code/docs, contracts, ADRs | Never replace source with a summary; preserve version and digest |
| T1 durable operational evidence | Accepted state and proof | `runtime/**`, receipts, evidence bundles, deployment or board readback | Retain identities, timestamps, source refs, and authority classification |
| T2 durable imports and artifacts | Governed evidence and large outputs | `data/**`, `packages/**`, artifact stores selected later | Preserve immutable bytes or explicit transformations with lineage |
| T3 derived indexes and read models | Retrieval acceleration and advisory synthesis | Cortex catalogs, symbol indexes, semantic or graph projections | Rebuildable from T0-T2; never becomes authority by convenience |
| T4 working context | Bounded task and conversation context | context packets, active plans, transient summaries | Compact only with source refs, unresolved risks, supersession, and replay path |
| T5 disposable state | Safe-to-delete work products | `tmp/**`, ephemeral previews, scratch captures | No durable truth may depend on retention |

Compaction principles:

- bind every summary to source references, digests, scope, and timestamp;
- preserve decisions, dissent, unresolved risks, and authority qualifiers;
- record supersession instead of silently rewriting prior evidence;
- keep retrieval indexes rebuildable and backend-neutral;
- do not hydrate private or raw imported evidence unless policy permits;
- treat missing or denied evidence as unknown, never as healthy or empty;
- require human review before derived memory becomes policy or doctrine.

Backend admission is deferred until measured retrieval quality, scale,
reliability, privacy, cost, backup, restore, migration, and operator burden
prove that current native files and indexes no longer suffice.

## Repository ingestion and compatibility graph candidate

**RECONCILED TARGET** pipeline:

```text
component manifests, package manifests, lockfiles, changelogs, and OpenAPI
-> deterministic file inventory and syntax/indexing
-> LSP symbols, references, diagnostics, and selected static analysis
-> dependency, API, schema, contract, and provenance compatibility graph
-> migration/adaptation plan with risks and rollback
-> CI matrix, contract tests, generated adapters, and evidence bundle
```

The pipeline must:

- identify repo owner, default source, revision, language mix, and exclusions;
- preserve generated/source distinctions and lockfile truth;
- record parser, language-server, and analyzer versions;
- distinguish observed compatibility facts from model inference;
- support partial results with explicit unsupported or unknown classes;
- generate adapters only behind tests and review;
- keep Tree-sitter, CodeQL, specific graph databases, and similar products as
  implementation candidates rather than required architecture.

## Policy, permission, and approval

**VERIFIED CURRENT ATLAS**:

- host permission describes what the execution environment can technically do;
- a JobEnvelope describes the bounded task and allowed paths;
- an ApprovalRecord carries explicit authority for sensitive action;
- owner contracts determine who may change owner truth;
- production deploy approval is current-thread, per project, and per deploy;
- DiscordOS remains one logical external writer;
- execution receipts prove outcomes but do not self-approve them.

Therefore full local host capability is not external mutation authority,
production authority, purchasing authority, board authority, or device
actuation authority. Voice, autonomy, planner confidence, and model capability
do not weaken this distinction.

## Staged roadmap

The roadmap is gated by current Atlas preparation and by independent lane
evidence. Dates and percentages are intentionally absent.

| Stage | Target | Entry gate | Exit evidence |
| --- | --- | --- | --- |
| 0. Preparation and ratification | Complete the current preparation cluster, closing audit, candidate admission, and operator success/kill decisions | Current Atlas gate contract | Accepted gate evidence; every preparatory gap separately closed |
| 1. Software builder | Repository ingestion, governed plan/edit/test/preview, durable context, artifact provenance | Product definition, metrics, policy, bootstrap, memory, and ingestion contracts admitted | Repeated accepted end-to-end builder scenarios on explicit repository classes |
| 2. Voice and creative loop | Low-latency exploration, interruption, inline preview, deterministic handoff to builder loop | Builder loop trusted and measured; realtime privacy and approval contract accepted | Measured creative-to-builder conversion, latency, trust, and failure recovery |
| 3. Spatial blueprint surface | Dependency/system/scene blueprint views; 2D before headset-specific work | Builder and visualization use case proves value | Repeated task improvement without roadmap or performance regression |
| 4. Device gateway and safe actuation | Read-mostly device model, simulation, then gated reversible actuation | Safety case, simulator, approval, rollback, and owner/device contracts | Accepted safe scenarios with zero unreceipted actuation |
| 5. Scale | Team, enterprise, provider, tenancy, and platform expansion | Proven demand and native limits | Measured reliability, security, cost, retention, and migration evidence |

## Success metrics and kill criteria

All thresholds are **DEFERRED DECISION** items requiring operator ratification.
The target architecture defines measurement placeholders, not completion.

| Decision area | Measurement unit | Baseline | Success threshold | Kill or narrow criterion |
| --- | --- | --- | --- | --- |
| First wedge reality | accepted end-to-end project outcome | unresolved | unresolved | stop or narrow if the builder cannot repeatedly ship a bounded useful artifact |
| Builder reliability | accepted scenarios / attempted scenarios by repo class | unresolved | unresolved | stop expansion when failures are non-reproducible, unsafe, or review cost exceeds value |
| Quality | escaped defects and rollback events per accepted change | unresolved | unresolved | narrow supported repos or artifact types when regression cost is unacceptable |
| User trust | rejected actions, authority violations, and recovery success | unresolved | unresolved | immediate hold on any unreceipted external or production mutation |
| Voice usefulness | creative-to-builder conversion and interaction latency | unresolved | unresolved | defer realtime expansion if voice adds novelty without task improvement |
| Retention | retained weekly users or repeated operator use | unresolved | unresolved | stop feature expansion when repeat use does not materialize |
| Monetization | paid outcomes, conversion, and gross margin by workload | unresolved | unresolved | reject pricing or infrastructure that cannot support the proven workload |
| Spatial value | task-time or comprehension improvement | unresolved | unresolved | keep spatial read-only or defer if it steals the software-builder roadmap |
| Device value and safety | accepted read/simulate/actuate scenarios | unresolved | unresolved | prohibit actuation after any unresolved safety, rollback, or identity failure |

The unmeasured candidate registry is the planning authority for ratifying these
units and denominators. No metric receives a percentage from this document.

## Adoption boundaries

- **RECONCILED TARGET** is architecture direction, not deployed truth.
- **EXTERNAL RESEARCH INPUT** remains lower authority than current Atlas and
  owner evidence.
- **DEFERRED DECISION** items require their own research, ADR, owner, evidence,
  migration, rollback, and acceptance path.
- **REJECTED/NOT ADOPTED NOW** items may reopen only from a new evidence-backed
  scope decision, not from repetition in research prose.
