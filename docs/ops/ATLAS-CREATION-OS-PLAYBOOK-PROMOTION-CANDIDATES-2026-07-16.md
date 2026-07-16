# Atlas Creation OS Playbook Promotion Candidates - 2026-07-16

## Status

This packet contains six Atlas-owned `atlas.knowledge-candidate.v2` review
candidates and one deferred Atlas product Decision. They are not adopted
Playbook doctrine, do not mutate the Playbook repository, and grant no
automatic promotion authority.

The six contract candidates must preserve exact identity, statement, scope,
evidence, and supported destination through Playbook's candidate-only review
path. The Decision is not a `KnowledgeCandidate` kind and cannot flow through
that contract without a separately approved Atlas Contracts and Playbook
consumer migration. It must not be relabeled. Playbook remains the doctrine
owner.

## Intended Playbook intake

- Candidate intake: Playbook's governed `atlas.knowledge-candidate.v2`
  consumer and dedicated review queue.
- Accepted candidate destinations are fail-closed by kind:
  `rule -> Playbook/rules`, `pattern -> Playbook/patterns`, and
  `failure-mode -> Playbook/failure-modes`.
- Required owner action: accept, revise, split, or reject each candidate with a
  correlated receipt; do not bulk-copy this packet.
- Root projection:
  [Creation OS KnowledgeCandidate manifest](../../data/knowledge-candidates/creation-os/manifest.v1.json).
- Owner handoffs:
  [Playbook candidate intake](ATLAS-CREATION-OS-PLAYBOOK-CANDIDATE-INTAKE-HANDOFF-2026-07-16.md)
  and
  [Cortex advisory refresh](ATLAS-CREATION-OS-CORTEX-ADVISORY-REFRESH-HANDOFF-2026-07-16.md).
- Required evidence:
  [Creation OS reconciliation](../audits/ATLAS-CREATION-OS-RESEARCH-RECONCILIATION-2026-07-16.md),
  [target architecture](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md),
  [current operating model](../atlas-book/03-operating-model.md), and
  [Atlas Contracts v2](../architecture/ATLAS-CONTRACTS-V2-SCOPE.md).

## Candidates

### `creation-os-human-directed-authority`

- Kind: RULE
- Statement: Atlas remains human-directed; autonomy does not imply external or
  production authority.
- Scope: Atlas jobs, tools, agents, voice surfaces, planner roles, deployments,
  publications, purchases, and device actions.
- Intended Playbook destination: `Playbook/rules`.
- Evidence:
  [Atlas Contracts authority boundaries](../architecture/ATLAS-CONTRACTS-V2-SCOPE.md#authority-boundaries),
  [target policy boundary](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#policy-permission-and-approval),
  and raw research lines 5, 19, 68, and 365-370.
- Review state: candidate; owner ratification required.

### `creation-os-bootstrap-pointer-not-memory`

- Kind: RULE
- Statement: The bootstrap artifact is a pointer into governed truth, never
  the entire memory system.
- Scope: recovery, profile/context bootstrap, memory, indexes, storage, and
  cross-machine restore.
- Intended Playbook destination: `Playbook/rules`.
- Evidence:
  [bootstrap ADR candidate](../atlas/decisions/adr-signed-versioned-atlas-bootstrap-manifest.md),
  [state and memory boundaries](../architecture/STATE-AND-MEMORY-BOUNDARIES.md),
  and raw research lines 7 and 218.
- Review state: candidate; implementation choices unresolved.

### `creation-os-builder-creative-loop-separation`

- Kind: PATTERN
- Statement: Separate the deterministic builder loop from the conversational
  creative loop and require explicit admission from creative output into
  governed execution.
- Scope: voice/text exploration, plans, code edits, tests, previews, receipts,
  merge, deploy, and publication.
- Intended Playbook destination: `Playbook/patterns`.
- Evidence:
  [target interaction loops](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#interaction-loops),
  [current native workflow](../architecture/ATLAS-CHATGPT-CODEX-WORKFLOW.md),
  and raw research lines 9 and 246.
- Review state: candidate; end-to-end owner proof still required.

### `creation-os-platform-surface-vertical-contracts`

- Kind: PATTERN
- Statement: Core platform, surfaces, and verticals evolve independently
  through explicit versioned contracts and owner boundaries.
- Scope: Atlas root, Playbook, Contracts, Cortex, `_stack`, DiscordOS, owner
  repositories, user surfaces, and domain products.
- Intended Playbook destination: `Playbook/patterns`.
- Evidence:
  [target ownership](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#current-truth-and-target-ownership),
  [System Ownership](../atlas-book/06-system-ownership.md),
  [Contracts And Seams](../atlas-book/07-contracts-and-seams.md),
  and raw research lines 23-27.
- Review state: candidate; no owner transfer authorized.

### `creation-os-infrastructure-shopping-before-wedge`

- Kind: FAILURE MODE
- Statement: Infrastructure shopping before the native-first wedge is proven
  turns a vendor list into architecture, creates operational burden, and hides
  the product-learning loop.
- Scope: databases, vector/graph stores, caches, object stores, workflow
  engines, realtime transports, policy engines, signing systems, and provider
  routers.
- Intended Playbook destination: `Playbook/failure-modes`.
- Evidence:
  [reconciliation decisions](../audits/ATLAS-CREATION-OS-RESEARCH-RECONCILIATION-2026-07-16.md#recommendation-mapping),
  [target non-goals](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#phase-one-non-goals),
  and raw research lines 222-228 and 260-271.
- Review state: candidate; vendor research remains external input.

### `creation-os-xr-device-novelty-trap`

- Kind: FAILURE MODE
- Statement: XR or device novelty consumes the software-builder roadmap before
  the first wedge has repeatable value, trust, and safe execution evidence.
- Scope: spatial viewers, headsets, scene standards, smart-home protocols,
  robotics, sensors, actuators, and hardware support.
- Intended Playbook destination: `Playbook/failure-modes`.
- Evidence:
  [staged target roadmap](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#staged-roadmap),
  [success and kill placeholders](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#success-metrics-and-kill-criteria),
  and raw research lines 11, 248-250, 355-356, and 369-370.
- Review state: candidate; spatial and device lanes remain deferred.

### `creation-os-software-repo-voice-first-wedge`

- Kind: DECISION
- Statement: Software creation with repository ingestion and voice is the first
  Creation OS product wedge, subject to operator ratification of success and
  kill metrics.
- Scope: product definition, repository classes, artifact types, previews,
  voice interaction, human approval, product-market fit, and monetization.
- Intended Playbook destination: none. This is an Atlas product Decision,
  outside the current `atlas.knowledge-candidate.v2` kinds and Playbook
  consumer mapping. Retain its source links to the Atlas target architecture
  and success/kill criteria.
- Evidence:
  [phase-one wedge](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#phase-one-wedge),
  [metric placeholders](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#success-metrics-and-kill-criteria),
  and raw research lines 13, 27, and 415.
- Review state: candidate; operator success/kill ratification required.

## Promotion gate

The later owner sequence must:

1. send exactly the six Rules, Patterns, and Failure Modes through the accepted
   candidate-only contract;
2. keep `creation-os-software-repo-voice-first-wedge` as a deferred Atlas
   product Decision outside `atlas.knowledge-candidate.v2`;
3. preserve Atlas evidence references, candidate identity, and artifact hash;
4. compare the six candidates against existing Playbook doctrine to avoid
   duplicates or conflicts;
5. return a Playbook owner receipt for accept, revise, split, or reject for
   each candidate, without bulk-copy or automatic doctrine promotion;
6. run Playbook owner validation and reconcile its receipt before the Cortex
   advisory refresh;
7. avoid marker movement unless a separate authorized marker audit accepts
   measured implementation evidence.

The exact next packet is `Playbook Creation OS candidate-only owner adoption`.
