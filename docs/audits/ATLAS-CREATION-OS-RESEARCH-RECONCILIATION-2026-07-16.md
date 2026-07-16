# Atlas Creation OS Research Reconciliation - 2026-07-16

## Result

The operator-provided Creation OS report is admitted as **EXTERNAL RESEARCH
INPUT** and preserved byte-for-byte. Compatible architectural direction is
reconciled into an Atlas-owned target, while vendor choices, implementation
claims, schedules, staffing, cost estimates, and market comparisons remain
non-canonical research input.

This packet changes no owner repository, runtime, external system, production
surface, or marker percentage. It deploys no infrastructure.

## Evidence classes

- **VERIFIED CURRENT ATLAS**: supported by current Git, validated Atlas
  artifacts, owner evidence, or explicit current readback.
- **EXTERNAL RESEARCH INPUT**: a claim or recommendation retained from the raw
  report; it is not current Atlas truth.
- **RECONCILED TARGET**: compatible direction adopted into Atlas planning but
  not claimed as implemented.
- **DEFERRED DECISION**: requires measurement, an ADR, operator ratification,
  or a later development gate.
- **REJECTED/NOT ADOPTED**: intentionally excluded from the current Atlas
  target or first wedge.

## Source and trust boundary

- Raw evidence: [Creation OS deep-research report](../../data/imports/creation-os/deep-research-2026-07-16/deep-research-report.md)
- Import manifest: [governed import manifest](../../data/imports/creation-os/deep-research-2026-07-16/IMPORT-MANIFEST.json)
- Source fingerprint: `39592` bytes, `415` lines, SHA-256
  `6d3ecbfba3cb22e9a29a30d00befaf7c4ac04720b8a619fc19a8e61e6f52fe8f`
- Trust class: `external-research-input`
- Review status: `reconciled-not-canonical`

The raw report contains citation artifacts and time-sensitive vendor or product
claims. Those claims remain attributed external input. This reconciliation
does not restate them as current canonical facts and does not depend on them to
describe current Atlas architecture.

## Verified current Atlas baseline

1. **VERIFIED CURRENT ATLAS** - Atlas root owns governance, markers, contracts,
   accepted receipts, and cross-repo projection; it is not an owner-product
   implementation repo. Evidence:
   [System Ownership](../atlas-book/06-system-ownership.md) and
   [Operating Model](../atlas-book/03-operating-model.md).
2. **VERIFIED CURRENT ATLAS** - `_stack` owns governed execution and delivery
   actions; Playbook owns doctrine and repo verification; Cortex remains
   advisory context, routing, and synthesis; DiscordOS remains the one logical
   board/publication/readback writer; owner repositories retain product and
   code truth. Evidence:
   [System Ownership](../atlas-book/06-system-ownership.md),
   [Contracts And Seams](../atlas-book/07-contracts-and-seams.md), and
   [Atlas, Cortex, Playbook, and Codex](../architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md).
3. **VERIFIED CURRENT ATLAS** - Native ChatGPT and Codex tasks are current
   command and execution transports; durable contracts and receipts provide
   the reverse handoff. Evidence:
   [The New Atlas Workflow](../architecture/ATLAS-CHATGPT-CODEX-WORKFLOW.md).
4. **VERIFIED CURRENT ATLAS** - Code, doctrine, retained runtime state,
   disposable state, durable imports, packages, and secrets already have
   separate path and authority classes. Evidence:
   [State and Memory Boundaries](../architecture/STATE-AND-MEMORY-BOUNDARIES.md)
   and [Path Policy](../architecture/PATH-POLICY.md).
5. **VERIFIED CURRENT ATLAS** - Atlas Contracts already defines identity,
   context, lease, evidence, receipt, approval, marker, and knowledge-candidate
   semantics. Full host capability is distinct from external mutation and
   production authority. Evidence:
   [Atlas Contracts v2 Scope](../architecture/ATLAS-CONTRACTS-V2-SCOPE.md).
6. **VERIFIED CURRENT ATLAS** - The post-preparation development program and
   its mandatory pre-development gate already exist. Creation OS planning must
   extend that program, not replace it. Evidence:
   [Vision And Endgames](../atlas-book/13-vision-and-endgames.md) and
   [Operating Model](../atlas-book/03-operating-model.md#post-preparation-development-program).

## Recommendation mapping

| Research recommendation | Report reference | Disposition | Atlas reconciliation |
| --- | --- | --- | --- |
| Human-directed durable agent platform | lines 5, 17-27, 68 | **RETAIN / RECONCILED TARGET** | Human direction and explicit authority remain kernel rules. "Agent platform" is interpreted as governed composition across existing Atlas owners, not a new monolith. |
| Native-first composition | lines 5, 21, 31, 256-271 | **RETAIN / RECONCILED TARGET** | Reuse current Atlas, ChatGPT, Codex, GitHub, Vercel, Supabase, and owner-native capabilities while they remain proven. New dependencies require measured need and bounded adoption. |
| Durable identity, contracts, receipts, and artifact provenance | lines 68-70, 109-115, 177-195, 365-370 | **RETAIN / RECONCILED TARGET** | Reuse Atlas Contracts identities, evidence bundles, receipts, approvals, checksums, and source hierarchy. |
| Deterministic builder loop and conversational creative loop | lines 9, 27, 246 | **RETAIN / RECONCILED TARGET** | Keep separate loops with an explicit promotion seam: conversational exploration cannot mutate governed truth until admitted to the deterministic builder loop. |
| Core platform, surfaces, and verticals evolve separately | lines 23-27 | **RETAIN / RECONCILED TARGET** | Define contract boundaries so platform capabilities, user surfaces, and domain products can evolve without owner collapse. |
| Repository ingestion and compatibility graph | lines 230-243 | **RETAIN / RECONCILED TARGET** | Adopt the pipeline shape: manifests, lockfiles, and OpenAPI -> syntax/indexing -> LSP/static analysis -> compatibility graph -> CI matrix and adapters. Named tools remain candidates. |
| Spatial and device expansion after the software wedge | lines 11, 248-250, 333-344, 369-370 | **RETAIN / DEFERRED DECISION** | Preserve staged spatial and device lanes, but keep them behind builder-loop trust, product evidence, safety contracts, and operator admission. |
| Reversible and gated side effects | lines 68, 365-370 | **RETAIN / RECONCILED TARGET** | Diff-first execution, explicit approvals, receipts, rollback, and safe actuation remain mandatory. |
| Signed bootstrap manifest as the permanent root pointer | lines 7, 218 | **RECONCILE / RECONCILED TARGET** | Use a signed, versioned, minimal recovery pointer into Atlas's distributed source hierarchy and memory boundaries. It is not a substitute for memory. See the [ADR candidate](../atlas/decisions/adr-signed-versioned-atlas-bootstrap-manifest.md). |
| One planner/PM agent | lines 41-68 | **RECONCILE / RECONCILED TARGET** | Treat planner/PM as a role spanning ATLAS MAIN intent, Cortex advisory planning, Atlas governance, and `_stack` execution contracts. Do not create a competing owner or grant automatic mutation authority. |
| Structured memory fabric | lines 7, 70, 137-153, 218-228, 366 | **RECONCILE / RECONCILED TARGET** | Preserve current Git/docs/runtime/data/receipt boundaries; add tiering, compaction, retrieval, and provenance contracts before selecting storage backends. |
| PostgreSQL, Qdrant, Neo4j, Redis, MinIO | lines 222-228, 260-271 | **RESEARCH/ADR / DEFERRED DECISION** | No backend is selected or deployed. Measure native gaps, scale, retrieval quality, operational burden, migration, rollback, and cost first. |
| LangGraph, Temporal, LiveKit, OPA, Cosign, Argo CD, provider routing | lines 252-294 | **RESEARCH/ADR / DEFERRED DECISION** | These remain attributed candidates. Current native primitives and owner capabilities retain priority until evidence proves a gap. |
| XR, OpenUSD/OpenXR, device gateways, robotics | lines 11, 248-250, 333-340 | **DEFER / DEFERRED DECISION** | Keep roadmap placeholders only. No XR or device infrastructure is admitted now. |
| Broad multi-provider routing and enterprise scale | lines 258, 273-284, 342-344 | **DEFER / DEFERRED DECISION** | Avoid phase-one provider abstraction beyond explicit contract seams. Admit later only from measured reliability, privacy, cost, or customer requirements. |
| Monolithic AGI framing | lines 5, 17-25 | **REJECTED/NOT ADOPTED** | Atlas remains a human-directed, contract-composed system with explicit owner boundaries. |
| Custom infrastructure because it appears in the report | lines 222-228, 260-271 | **REJECTED/NOT ADOPTED** | A vendor list is not an architecture decision or deployment authorization. |
| Single-file all-memory model | lines 7, 218 | **REJECTED/NOT ADOPTED** | The bootstrap artifact is a recovery pointer, never the memory system. |
| Simultaneous build of every surface | lines 13, 307, 311-345, 364 | **REJECTED/NOT ADOPTED** | The first wedge is software creation; later surfaces are gated, independently measured lanes. |
| Replacing proven native ChatGPT/Codex transport now | report lines 5 and 264-284, reconciled against current Atlas evidence | **REJECTED/NOT ADOPTED NOW** | Preserve current native transport. Cortex replacement remains an evidence-backed later migration, not a prerequisite for the wedge. |

## Adopted durable direction

The reconciled target is defined in
[Atlas Creation OS Target Architecture](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md):

- a human-directed Creation OS;
- a voice-capable software, app, and tool builder as the first wedge;
- repository ingestion, bounded execution, tests, previews, durable context,
  evidence, and human authority;
- independent platform, surface, and vertical contracts;
- a deterministic builder loop separated from a conversational creative loop;
- a signed/versioned bootstrap recovery pointer;
- backend-neutral memory tiers and provenance-preserving compaction;
- staged software builder -> voice/creative -> spatial -> device -> scale work;
- explicit unresolved success thresholds and kill criteria.

## Decisions not made

- No database, vector store, graph store, cache, object store, workflow engine,
  realtime transport, policy engine, artifact signer, XR standard, or device
  protocol is selected.
- No deployment target, model provider, team size, schedule, budget, pricing,
  retention target, or product-market-fit threshold is ratified.
- No deployed memory fabric or bootstrap manifest implementation is claimed.
- No external or production authority is granted.

## Post-work review

- Duplication: the target architecture extends, links, and summarizes the
  current Atlas operating model; it does not replace chapters 3, 13, or 16.
- Authority: all owner repositories retain their existing implementation
  truth; Playbook promotion remains candidate-only.
- Source of truth: current Git and validated Atlas artifacts outrank the raw
  report and this narrative reconciliation.
- Marker integrity: ten Creation OS candidates are unmeasured; no percentage,
  completed unit, or denominator is inferred.
