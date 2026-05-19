# Verta-Core Absorption Blueprint

## Purpose

Define the ATLAS root posture for absorbing Verta-Core into the ATLAS stack without collapsing owner-repo truth into the stack root.

This document is root-owned doctrine. It does not admit the raw Verta-Core checkout by itself, and it does not treat `repos/Verta-Core` as trusted runtime truth.

## Current Decision

- Do not absorb Verta-Core by copying implementation into the ATLAS root.
- Do not promote the raw `repos/Verta-Core` checkout or `repos/Verta-Core.zip`.
- Treat Verta-Core as quarantined provenance until one derivative owner surface is named explicitly.
- Route admitted behavior into the correct owner surface, or create a new admitted owner repo if no current repo is a clean fit.

## Non-Goals

- no silent promotion of `repos/Verta-Core` or `repos/Verta-Core.zip`
- no new runtime or deployment lane invented just for Verta-Core
- no root-owned app auth, DAL, or deploy implementation
- no cross-repo edits beyond the explicitly named participating repos

## Identity And Trust Rules

`Verta-Core` is currently a quarantined historical surface, not an admitted owner repo.

Rules:

- The standing Verta trust gate remains in force for `repos/Verta-Core` and `repos/Verta-Core.zip`.
- Historical Verta material may inform ATLAS-authored notes only with explicit provenance and visible untrusted posture.
- New Verta-derived material must start in a quarantine or metadata-only lane until scrub and classification complete.
- No imported Verta-Core code, scripts, hooks, installers, or background workers should be executed during intake.

## Topology Coherence Gate

Do not register the first Verta-derived owner surface against drifting stack metadata.

Before Phase 0 derivative admission, confirm that the live checkout agrees across:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `README-STACK.md`
- `docs/ops/STACK-OWNER-USAGE-MATRIX.md`

The minimum requirement is that participating repo ids, excluded surfaces, and the current quarantine posture match closely enough that ownership decisions are trustworthy.

Phase `-1` completion note:

- Rule: Verta-Core absorption admits derivatives, never the raw archive or raw checkout.
- Pattern: ATLAS root owns topology, contracts, doctrine, and projection; owner repos own executable behavior.
- Failure mode: admitting a Verta-derived seam against drifting topology creates false certainty and can route ownership to the wrong repo.
- Receipt path: use `runtime/receipts/validation/stack-validation.latest.md` and `runtime/receipts/validation/stack-validation.latest.json` as the current topology-coherence evidence surfaces.
- Phase 0 remains blocked until `stack.yaml`, `stack.lock.yaml`, the published inventory, `README-STACK.md`, and `docs/ops/STACK-OWNER-USAGE-MATRIX.md` agree on governed repos, deferred adjacent surfaces, and the standing Verta quarantine posture.

## Root Versus Owner Boundary

ATLAS root owns:

- contract versions under `packages/atlas-contracts`
- admission doctrine and repo-class policy
- stack-level runbooks, audits, and migration notes
- registry and read-model visibility under `docs/registry` and root runtime catalogs

Owner repos own:

- application code
- app auth and DAL behavior
- repo-local deployment configuration
- app-specific health production
- app-specific event payloads and receipts

## Landing Zone Matrix

| Verta-derived concern | Default ATLAS destination | Notes |
| --- | --- | --- |
| intake, quarantine, provenance, scrub evidence | `data/imports/knowledge/**` plus `docs/knowledge/reviews/**` | Keep raw evidence immutable and metadata-first |
| shared contract normalization | ATLAS root | Normalize only federated seams, not all internal types |
| app admission metadata | ATLAS root plus owner repo registration | Use `atlas.app-registration.v1` before promotion |
| reusable workflow, repo intelligence, deterministic CLI logic | `playbook` | Only if the logic is genuinely cross-repo and reusable |
| operator runtime, startup, deploy manifest, release activation, rollback | `lifeline` | Prefer manifest and receipt-driven rollout over ad hoc scripts |
| orchestration, worker, merge, resume, session coordination | `_stack` | Use when the absorbed capability is workflow-operator behavior |
| product UI, app routes, domain logic, repo-local data access | existing application repo or a new admitted application repo | Do not force a semantic mismatch into root, Playbook, or Lifeline |
| read-only stack visibility and migration status | ATLAS root registry and awareness surfaces | No separate control-plane repo is assumed here unless later admitted |
| unsafe or unresolved historical material | remain quarantined | Do not promote because it is useful or familiar |

## Repo Class Decision Rules

Choose the narrowest class that matches the admitted surface:

- `application`: user-facing app or service behavior
- `governance-runtime`: reusable governance, deterministic workflow, or repo intelligence
- `local-operator`: operator runtime, deploy control, release activation, rollback, bounded execution
- `workflow-operator`: orchestration, workers, merge, resume, or coordination behavior
- `incubating`: partially shaped repo not ready for managed promotion
- `quarantined`: untrusted intake, secret-bearing material, or unresolved provenance
- `archive`: historical material with no active ownership claim

Decision rule:

- If no current repo can own the admitted behavior cleanly, create a new owner repo and admit it through the normal repo-class path.

## Required Contracts Before Promotion

Before a Verta-derived owner surface can move beyond `incubating`, it should have:

- `atlas.app-registration.v1`
- `atlas.env.v1`
- `atlas.health.v1`
- `atlas.event.v1` when platform-visible events exist
- `atlas.receipt.v1` when platform-visible receipts exist

Promotion also requires:

- one documented repo-local validation entrypoint
- explicit owner-repo routing
- explicit deployment lane selection
- explicit trust posture for any retained historical imports

## First Admitted Seam

The first real absorption step should be one derivative owner surface, not the raw archive.

Phase 0 target:

- identify one concrete Verta-derived behavior worth keeping
- declare its owner repo explicitly
- export a repo-owned `atlas.app-registration.v1`
- document at least one owner-repo validation entrypoint
- keep the raw Verta checkout and zip quarantined as provenance only

Current Phase 0 selection:

- owner repo: `playbook`
- derivative seam: `verta-derivative-pattern-pack`
- artifact boundary: reviewed derivative governance and pattern docs only
- provenance refs: `docs/knowledge/promotions/atlas--verta-historical-playbook-principles-20260417.md`, `docs/knowledge/promotions/atlas--verta-historical-convergence-intent-20260417.md`, `docs/knowledge/reviews/verta-core.md`, `docs/knowledge/reviews/verta-core-scrub-report.md`
- owner-surface contract note: `repos/fawxzzy-playbook/docs/contracts/VERTA_DERIVATIVE_PATTERN_PACK.md`
- explicit non-goal: no executable Verta behavior, no raw source promotion, no Foundation admission
- review gate: Phase 0 is not complete until the Playbook derivative artifact is promotion-ready with explicit provenance, trust boundary, review state, and verification evidence
- downstream gate: no adapter, parity, or runtime-execution phase may begin from this seam until a reviewed Playbook derivative artifact exists and a separate executable seam is explicitly selected

## Migration Model

Use a contract-first strangler shape:

1. Quarantine intake and secret scrub.
2. Freeze ownership, repo class, and contract seams.
3. Add adapters for health, events, receipts, config extraction, and traffic steering.
4. Prove parity with shadow reads, dual writes where needed, and migration validation.
5. Cut over progressively with a bounded rollback window.
6. Archive or retire only after stabilization evidence exists.

Default rule:

- The first code move should usually be an adapter at the seam, not a rewrite of the full legacy surface.

## Deployment Selection

Verta-derived behavior should reuse one of the delivery patterns already present in the stack:

- application-style web delivery in the owning app repo
- static-export delivery for static catalog or storefront behavior
- Lifeline-managed single-host or operatorized delivery when rollout, release, and rollback need local-operator semantics

Do not introduce a fourth deployment model until an existing lane is proven insufficient.

## Promotion Gates

Promotion from intake to active ownership should stay blocked until all of the following are explicit:

- identity and provenance
- owner repo or new repo decision
- contract boundary
- verify entrypoint
- deployment lane
- secret posture and any required rotation
- rollback plan
- acceptance evidence

For the current Playbook-owned seam, moving beyond Phase 0 additionally requires:

- Playbook verification and docs audit receipts
- explicit review of the derivative pattern pack against its provenance refs
- explicit confirmation that the derivative pack is the reviewed intake surface for admitted, rejected, and pending Verta-derived patterns
- a later decision on whether any adapter, parity, or execution lane is needed at all

## Practical Consequence

Absorb Verta-Core by derivative admission, not by raw checkout promotion or root-level consolidation.
