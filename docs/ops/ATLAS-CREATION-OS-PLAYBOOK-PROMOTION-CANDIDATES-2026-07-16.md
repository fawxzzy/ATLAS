# Atlas Creation OS Playbook Promotion Candidates - 2026-07-16

## Status

These are Atlas-owned review candidates for a later Playbook owner packet.
They are not adopted Playbook doctrine, do not mutate the Playbook repository,
and grant no automatic promotion authority.

Candidate admission must preserve exact statement, scope, evidence, and
suggested destination through the Atlas `KnowledgeCandidate` contract and
Playbook's candidate-only review path. Playbook remains the doctrine owner.

## Intended Playbook intake

- Candidate intake: Playbook's governed `atlas.knowledge-candidate.v2`
  consumer and dedicated review queue.
- Intended canonical destination after owner review:
  `repos/playbook/docs/doctrine/atlas-engineering-doctrine-registry.v1.json`.
- Required owner action: accept, revise, split, or reject each candidate with a
  correlated receipt; do not bulk-copy this packet.
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
- Intended Playbook destination: doctrine registry, authority and approvals
  family.
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
- Intended Playbook destination: doctrine registry, state/memory and recovery
  family.
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
- Intended Playbook destination: doctrine registry, execution workflow family.
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
- Intended Playbook destination: doctrine registry, architecture and ownership
  family.
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
- Intended Playbook destination: doctrine registry, architecture decision and
  scope-control family.
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
- Intended Playbook destination: doctrine registry, roadmap and scope-control
  family.
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
- Intended Playbook destination: doctrine registry, product decision family;
  retain a source link to the Atlas target architecture.
- Evidence:
  [phase-one wedge](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#phase-one-wedge),
  [metric placeholders](../architecture/ATLAS-CREATION-OS-TARGET-ARCHITECTURE.md#success-metrics-and-kill-criteria),
  and raw research lines 13, 27, and 415.
- Review state: candidate; operator success/kill ratification required.

## Promotion gate

The later Playbook owner packet must:

1. ingest each candidate through the accepted candidate-only contract;
2. preserve Atlas evidence references and candidate identity;
3. compare against existing Playbook doctrine to avoid duplicates or conflicts;
4. return an owner receipt for accept, revise, split, defer, or reject;
5. run Playbook owner validation;
6. avoid marker movement unless a separate authorized marker audit accepts
   measured implementation evidence.

The exact next packet is `Playbook Creation OS doctrine adoption and Cortex
refresh`.
