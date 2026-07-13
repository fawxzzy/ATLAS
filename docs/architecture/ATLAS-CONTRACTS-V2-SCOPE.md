# Atlas Contracts v2 Scope

## Purpose

Atlas Contracts v2 is the versioned interoperability mesh for governed work across Atlas, `_stack`, Cortex, Playbook, DiscordOS, and owner projects. Atlas root owns shared semantics and compatibility. Owner repositories own implementations and may add namespaced extensions without redefining shared meanings.

The existing private `@atlas/contracts` package remains version `0.1.0` and currently implements five v1 families: environment, app registration, health, event envelope, and receipt. Those contracts remain valid compatibility surfaces. They are not counted as completed v2 families until an explicit v2 schema, validator proof, and producer/consumer adoption proof exist.

## Fixed Denominator

The v2 mesh contains exactly eleven schema families:

| Family | Canonical responsibility |
|---|---|
| `ComponentManifest` | Component identity, role, ownership, repository path, capabilities, dependencies, and adopted protocol versions |
| `CardRecord` | Human-facing project work identity, type, lifecycle, priority, ownership, dependencies, and board version |
| `JobEnvelope` | Bounded objective, project/card correlation, runtime policy, permissions, authority, scope, verification, and expected receipt |
| `ContextPacket` | Provenance-bound architecture, rules, decisions, active state, risks, and task-relevant context |
| `WorkerLease` | Thread, worktree, branch, process, port, browser, resource ownership, expiry, renewal, and recovery |
| `EvidenceBundle` | Commands, tests, diffs, screenshots, source references, environment facts, and proof classifications |
| `ExecutionReceipt` | Terminal outcome, changed paths, commits, verification, blockers, follow-up work, and correlation identities |
| `BoardEvent` | Idempotent card creation, update, transition, blocker, completion, and readback intent/result |
| `MarkerEvidence` | Marker scope, numerator, denominator, evidence, freshness, transition, and non-rollup rules |
| `KnowledgeCandidate` | Proposed Rule, Pattern, Failure Mode, Automation Opportunity, or Governance Gap with provenance and review state |
| `ApprovalRecord` | Explicit authority for external mutation, production deployment, destructive action, sensitive operation, or exception |

## Identity Chain

```text
Component ID
-> Card ID
-> Atlas Job ID
-> Codex Thread / Turn ID
-> Worker Lease
-> Branch / Commit / PR
-> Evidence Bundle
-> Execution Receipt
-> Board Event
-> Marker Evidence
-> Knowledge Candidate
```

Not every job produces every object, but produced objects must retain the available upstream identities.

## Versioning

- Each family has an independent contract identifier and semantic version.
- Additive optional fields may remain compatible within a major version.
- Required-field removal, meaning changes, enum meaning changes, or lifecycle changes require a new major version.
- Consumers must reject unknown major versions unless an explicit compatibility adapter is registered.
- Shared enums and lifecycle meanings are Atlas-owned. Owner extensions use namespaced fields and cannot override shared semantics.
- A schema file alone is not adoption. Adoption requires a validated producer and consumer receipt.

## Existing v1 Compatibility

- `atlas.app-registration.v1` is a predecessor input to `ComponentManifest`, not an automatic v2 completion.
- `atlas.event.v1` remains the generic envelope that v2 event-bearing families may embed or reference.
- `atlas.receipt.v1` remains a generic receipt predecessor to `ExecutionReceipt`.
- `atlas.github.event-receipt.v1`, `atlas.github.event-admission.v1`, and `atlas.github.projection-intent.v1` define the canonical `_stack -> Atlas -> DiscordOS` GitHub projection seam and remain outside the eleven-family v2 denominator.
- `atlas.env.v1` and `atlas.health.v1` remain platform contracts outside the eleven-family denominator.
- Existing exports and fixtures remain supported until a separately approved migration proves consumers have moved.

## GitHub Projection Seam

The GitHub projection seam is intentionally contract-only:

```text
_stack normalized GitHub facts
-> atlas.github.event-receipt.v1
-> Atlas admission and deduplication
-> atlas.github.event-admission.v1
-> formatting-free atlas.github.projection-intent.v1
-> DiscordOS single writer
```

- `_stack` keeps immutable fact production and does not own Discord mutation.
- Atlas owns admission, durable correlation, backend-neutral ledger meaning, and intent production.
- DiscordOS owns final presentation, card/update mutation, publication, and readback.
- The seam preserves deterministic source identities (`ghr_`, `ghk_`) and adds Atlas-local admission and projection identities without weakening owner-repository truth or external-mutation authority.

## Implementation Order

1. `ComponentManifest`, `JobEnvelope`, `ExecutionReceipt`
2. `ContextPacket`, `EvidenceBundle`, `ApprovalRecord`
3. `WorkerLease`
4. `CardRecord`, `BoardEvent`
5. `MarkerEvidence`, `KnowledgeCandidate`

The first cluster establishes identity, execution intent, and terminal correlation. Later clusters must reuse those identities rather than invent parallel ones.

## Acceptance Per Family

A family counts as one completed unit only when all are true:

1. Versioned schema exists.
2. Public type/constants/export surface exists.
3. Valid and invalid fixtures exist.
4. Package validator proves both fixture classes.
5. Compatibility behavior is documented and tested.
6. At least one governed producer and one governed consumer emit accepted evidence.

Partial implementation remains zero for that family. The lane percentage is `completed families / 11`.

## Authority Boundaries

- Full local host capability does not grant external mutation or production authority.
- `ApprovalRecord` carries authority; it does not weaken permission profiles.
- `_stack` produces execution and delivery facts but does not own Discord presentation.
- DiscordOS owns board and Discord writes but cannot infer Git, deploy, or verification truth from prose.
- Cortex assembles context and recommendations but does not become execution authority.
- Chats and tasks are command surfaces, not durable contract stores.

## Non-Goals

- No custom agent execution queue
- No SQLite backend commitment
- No owner-repository logic moved into Atlas root
- No automatic production deployment authority
- No replacement of v1 before compatibility proof
- No percentage credit for schema prose without executable proof
