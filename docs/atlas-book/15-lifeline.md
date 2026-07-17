# Lifeline

## Purpose

This chapter is the durable ATLAS Book entry for Lifeline's role in the stack.

Use it to answer:

- what Lifeline owns
- what Lifeline consumes
- what Lifeline emits
- what is shipped now
- what remains planned later

This chapter is architecture-first and retrieval-first.

It is also the first concrete example of the ATLAS-side `ATLAS systems-doc normalization` pattern: owner-repo truth is reconciled into restart-friendly Book documentation here without moving repo-local command or implementation truth out of the Lifeline repo.

It does not replace the Lifeline repo README, architecture docs, runbooks, or repo-local contracts.

For command-level and implementation truth, use:

- [`repos/lifeline/README.md`](../../repos/lifeline/README.md)
- [`repos/lifeline/docs/architecture.md`](../../repos/lifeline/docs/architecture.md)
- [`repos/lifeline/docs/ops/lifeline-operator-surface.md`](../../repos/lifeline/docs/ops/lifeline-operator-surface.md)
- [`repos/lifeline/docs/startup-contract.md`](../../repos/lifeline/docs/startup-contract.md)

## Lifeline Role

Lifeline is the self-hosted, local execution/operator plane for manifest-defined applications.

Its current contract is intentionally narrow:

- local-first
- single-host
- deterministic
- receipt-emitting
- manifest-driven

Lifeline is not:

- a hosted platform
- a control plane
- a multi-node orchestrator
- a database platform

## Current Shipped Surfaces

"Shipped" in this section describes implemented Lifeline capability. Current
registration and restorable state are stated separately and do not imply that
the supervised Observer is running.

The current shipped Lifeline surface includes:

- manifest validation
- manifest resolution
- manifest-defined app lifecycle execution
- local runtime lifecycle execution
- Wave 1 runtime foundation
- deterministic execution on one machine
- bounded execution receipts
- release `plan`, `persist`, `activate`, and `rollback`
- release receipts
- proof-pass receipts
- worker `source_refs` preserved in receipts
- ATLAS-aligned receipt emission
- startup registration contract
- Playbook disk-only export consumption

Current shipped posture stays local and bounded:

- no hosted admin plane
- no multi-node runtime coordination
- no ambient privileged mutation
- no HTTP dependency on Playbook

## Current Local Availability

Merged Lifeline PR `#35` accepts build/doctor, state placement, bounded
supervised restart, and deterministic restore proof. Read-only probes on
2026-07-16 found:

- `LifelineRestoreAtLogon` enabled, `Ready`, and `LastTaskResult=0`
- the logon action bound to the root runtime home
  `runtime/lifeline/playbook-observer`
- Playbook Observer intentionally stopped/restorable, with no listener on port
  `4300`

This is registered/restorable posture, not running/healthy uptime proof. No
fresh actual later new-logon restoration or sustained unattended uptime was
observed in this reconciliation; both remain unknown. The next activation
packet is Cortex read-model refresh, not a Lifeline rerun.

## Planned Later Surfaces

These remain later surfaces, not current shipped truth:

- Vercel/service-health classification
- deploy provenance visibility
- stale-surface pressure signals
- broader ATLAS-facing health projection
- the `_stack` `vercel-health` seam as input to later Lifeline-facing health views
- richer ownership and deploy-health surfaces

Future health projection work must not be phrased as already implemented Lifeline runtime scope.

## Ownership Boundaries

### Lifeline

Lifeline owns:

- local execution
- manifest/runtime/release/startup/proof surfaces
- local receipt semantics for those execution surfaces
- repo-local implementation and verification truth

### ATLAS

ATLAS owns:

- retrieval spine
- markers
- cross-repo receipts
- cross-repo coordination

ATLAS may checkpoint Lifeline consequences, but it does not replace Lifeline as the owner of repo-local runtime or command truth.

### `_stack`

`_stack` owns:

- governed deploy authority
- shared operator execution wrappers
- later health-signal command seams that may feed Lifeline-facing read models

`_stack` does not own Lifeline runtime semantics.

### Playbook

Playbook owns:

- human workflow and export defaults
- disk-export production for Lifeline archetype defaults
- doctrine and reusable workflow framing

Playbook is not an HTTP dependency for Lifeline.

### Foundation

Foundation is:

- the existing hosted read-only portfolio surface
- independent of Lifeline's private loopback supervision path

Foundation is not a hard current runtime dependency for Lifeline's shipped operator boundary.

### Cortex

Cortex is a future consumer of durable planning and retrieval surfaces.

Cortex does not currently own or mutate Lifeline runtime behavior.

## Cross-System Seams

### Lifeline <-> Playbook

- Lifeline consumes optional Playbook exports from disk
- Playbook remains a human workflow and export producer
- no HTTP dependency is allowed in the current Lifeline surface

### Lifeline <-> ATLAS

- Lifeline emits deterministic receipts and proof-facing artifacts
- ATLAS records the cross-repo checkpoint and retrieval consequence
- ATLAS remains the retrieval spine, not the command owner

### Lifeline <-> `_stack`

- Lifeline runtime truth stays Lifeline-owned
- `_stack` remains the governed deploy authority
- later shared health-signal seams may inform Lifeline-facing health projection without moving runtime ownership

### Lifeline <-> Foundation

- Foundation is the hosted read-only portfolio, not a current required Lifeline runtime dependency
- any later adoption should preserve Lifeline's local-first, deterministic boundary

### Lifeline <-> Cortex

- Cortex may later consume Lifeline-facing planning context from durable surfaces
- Cortex does not currently define Lifeline runtime truth or execution authority

## Deployment And Execution Flow

The current bounded Lifeline flow is:

1. manifest loaded
2. optional Playbook defaults applied from disk
3. validation and resolution
4. runtime lifecycle execution
5. release `plan` / `persist` / `activate`
6. receipt emission
7. proof-pass alignment when ATLAS proof summaries are already clean
8. ATLAS checkpoint

This flow stays local-first and deterministic.

It does not imply:

- hosted deploy orchestration
- remote platform control
- multi-node rollout management

## Retrieval And Restart Order

When the task is Lifeline-specific, restart in this order:

1. this chapter for role, boundaries, seams, and shipped-vs-planned truth
2. the Lifeline repo truth surfaces for command-level behavior:
   - [`repos/lifeline/README.md`](../../repos/lifeline/README.md)
   - [`repos/lifeline/docs/architecture.md`](../../repos/lifeline/docs/architecture.md)
   - [`repos/lifeline/docs/ops/lifeline-operator-surface.md`](../../repos/lifeline/docs/ops/lifeline-operator-surface.md)
   - [`repos/lifeline/docs/startup-contract.md`](../../repos/lifeline/docs/startup-contract.md)
3. ATLAS receipts and markers for lane posture and cross-repo evidence

Do not restart a Lifeline lane from transcript memory first.

Do not treat the Book as a replacement for repo-local CLI, contract, or runbook truth.

## Rules, Patterns, And Failure Modes

Rule:
ATLAS owns retrieval; owner repos own repo-local truth.

Pattern:
Manifest -> optional Playbook defaults -> Lifeline execution -> deterministic receipts -> ATLAS checkpoint.

Failure Mode:
Lifeline drifts into hosted platform, admin plane, multi-node orchestrator, or generic data platform behavior before its narrow local operator contract is preserved.

## Related Book Surfaces

- [Current State](01-current-state.md)
- [System Ownership](06-system-ownership.md)
- [Current System Map / Graph](11-system-map-graph.md)
- [Restart And Handoff Guide](12-restart-and-handoff-guide.md)
