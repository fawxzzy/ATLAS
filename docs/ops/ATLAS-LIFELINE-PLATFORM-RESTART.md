# ATLAS Lifeline Platform Restart

This document captures the stack-owned restart posture for the Lifeline platform cutover lane.

It is a coordination artifact for the stack root, not a replacement for repo-owned implementation doctrine inside `repos/fawxzzy-lifeline`, `repos/fawxzzy-playbook`, or `repos/fawxzzy-atlas`.

Adoption note for the current root posture:

- Rule: ATLAS should federate Lifeline truth, not duplicate Lifeline truth.
- Pattern: Root docs should route operator intent to the owning repo.
- Failure Mode: Stack docs become a second truth store when root restates child-repo contracts instead of linking to them.

## Grounding

This restart is grounded in the current stack boundary rules and the recovered operating model:

- `README-STACK.md` defines the stack root as the coordination layer rather than an umbrella app repo.
- `stack.yaml` keeps `atlas`, `lifeline`, and `playbook` as separate owner repos with separate roles.
- `docs/architecture/PATH-POLICY.md` and `AGENTS.md` keep stack-root work boundary-oriented and relative-path safe.
- preserved project memory says the recoverable history is mostly operating-model guidance, not a hidden execution backlog.
- the most stable recovered decision is the separation:
  - Atlas = umbrella coordination
  - Lifeline = execution lane for platform cutover
  - Playbook = codification and governance lane

## Program Intent

This program exists to restart the Vercel-replacement path without letting Atlas absorb owner-repo execution.

The stack-root responsibilities are:

- keep milestone definitions explicit
- sequence repo-local work across lanes
- make ownership and non-goals unambiguous
- define parallel worker slices with minimal file overlap

The stack root does not own platform implementation details, deploy code, runtime manifests, or app cutover changes.

## Repo Ownership

### Atlas

Atlas owns:

- roadmap and milestone framing
- dependency tracking across lanes
- migration scoreboard shape
- cross-lane sequencing and escalation points

Atlas does not own:

- deploy implementation
- runtime plumbing
- rollback mechanics
- pilot-app cutover execution

### Lifeline

Lifeline owns the platform-cutover critical path:

- deploy and runtime contract
- environment and secrets model
- routing, TLS, and runtime baseline
- logs, health checks, and rollback posture
- pilot-app cutover
- parity criteria for exiting the old platform path

This is the owner lane for the milestone that matters: proving one meaningful app or service can run outside Vercel with explicit operational controls.

For execution-governance surfaces at the stack root, route to these Lifeline docs instead of re-authoring the contract locally:

- `repos/fawxzzy-lifeline/docs/contracts/privileged-execution-contract.md`
- `repos/fawxzzy-lifeline/docs/contracts/ui-proof-passed-receipt-contract.md`
- `repos/fawxzzy-lifeline/docs/ops/lifeline-operator-surface.md`
- `repos/fawxzzy-lifeline/docs/runbooks/hermetic-validation-operator-flow.md`

### Playbook

Playbook owns:

- decision logging
- failure-mode capture
- migration checklist extraction
- reusable patterns
- runbooks
- later automation and templates

Wave 1 posture:

- shadow Lifeline decisions
- codify what was learned without blocking Lifeline execution

Wave 2 posture:

- productize reusable onboarding, templates, and automation from proven Lifeline patterns

## Primary Milestone

Do not frame success as replacing Vercel everywhere.

Frame success as:

Trove runs on Lifeline with explicit parity criteria, health visibility, and a rehearsed rollback, and Vercel is no longer required for Trove.

That milestone is intentionally narrower because it produces evidence sooner and limits platform sprawl.

## Wave Structure

### Wave 1

Wave 1 proves the platform path through one pilot and keeps Playbook in shadow mode.

Required outcomes:

- a base runtime path exists
- a deploy contract exists
- operational checks exist
- one pilot app or service can run through the new path
- parity and rollback are explicit rather than implied

### Wave 2

Wave 2 only begins after the pilot is real and observable.

Expected expansion areas:

- reusable templates
- app onboarding patterns
- multi-service migration playbooks
- provisioning and deploy automation
- shared operator runbooks extracted from proven work

## Parallel Worker Lanes

Each lane is designed to minimize overlap and keep stack-root orchestration honest.

### Lane A: Runtime Foundation

Owner repo:

- `lifeline`

Scope:

- base host layout
- container and service model
- reverse proxy and TLS baseline
- application and runtime contract framing

Likely owner-repo surfaces:

- `infra/**`
- `runtime/**`

Definition of done:

- one stable runtime baseline is documented and testable inside Lifeline owner truth

### Lane B: Control Plane And Deploy Contract

Owner repo:

- `lifeline`

Scope:

- deploy command model
- release metadata
- environment and secret injection contract
- rollback target shape

Likely owner-repo surfaces:

- `control-plane/**`
- CLI or API deploy entrypoints

Definition of done:

- deploy and rollback flows are explicit enough to drive a pilot without operator folklore

### Lane C: Ops Baseline

Owner repos:

- `lifeline`
- `playbook` in shadow mode for codification only

Scope:

- health checks
- structured logs
- basic metrics or event visibility
- rollback runbook criteria

Likely owner-repo surfaces:

- `ops/**`
- health endpoints
- `docs/runbooks/**`

Definition of done:

- the pilot path has operational visibility and a written rollback threshold

### Lane D: Pilot App Migration

Owner repos:

- one selected application repo
- `lifeline` for the platform side of the cutover

Scope:

- choose one meaningful app or service
- wire platform config
- exercise deploy lifecycle
- compare behavior against the old platform path

Likely owner-repo surfaces:

- selected app repo `platform/**` or equivalent owner path
- Lifeline pilot-specific integration surfaces

Definition of done:

- one real pilot can be deployed, checked, and rolled back with explicit parity notes

### Lane E: Playbook Shadow Codification

Owner repo:

- `playbook`

Scope:

- capture decisions as they happen
- record failure modes and mitigations
- define the migration checklist
- extract reusable completion criteria

Definition of done:

- Lifeline discoveries are preserved as reusable doctrine without turning Playbook into the execution bottleneck

## Worker Prompt Templates

These prompts are for future repo-scoped worker sessions. They are intentionally ownership-based rather than implementation-prescriptive.

### Worker Prompt: Lifeline Runtime Foundation

Work only inside `repos/fawxzzy-lifeline`.

Own the runtime-foundation slice for the platform cutover lane. Define or refine the base host layout, service model, reverse-proxy and TLS baseline, and the app/runtime contract. Keep the slice bounded to runtime-foundation surfaces such as `infra/**` and `runtime/**`. Do not implement deploy control-plane logic, pilot-app app-specific wiring, or Playbook codification work. Verify with the Lifeline repo-local command before completion and report the exact files changed plus any unresolved contract assumptions.

### Worker Prompt: Lifeline Deploy Contract

Work only inside `repos/fawxzzy-lifeline`.

Own the deploy-contract slice for the platform cutover lane. Define or refine the deploy command model, release metadata contract, environment and secret injection path, and rollback target shape. Keep the slice bounded to control-plane or deploy-entry surfaces. Do not change runtime-foundation plumbing unless required by an explicit contract seam, and do not modify pilot-app repo files. Verify with the Lifeline repo-local command before completion and report the exact files changed plus any remaining rollback gaps.

### Worker Prompt: Lifeline Ops Baseline

Work only inside `repos/fawxzzy-lifeline`.

Own the ops-baseline slice for the platform cutover lane. Add or refine health checks, structured log expectations, basic metrics or event visibility, and rollback/runbook criteria needed for a pilot. Keep the slice bounded to Lifeline operational surfaces and do not take over Playbook codification. Verify with the Lifeline repo-local command before completion and report the exact files changed plus the operational signals the pilot can now rely on.

### Worker Prompt: Pilot App Migration

Work only inside the selected pilot repo plus `repos/fawxzzy-lifeline` if a paired platform change is required.

Own the pilot cutover slice. Choose or use the designated pilot app or service, wire its platform-facing configuration, exercise the deploy lifecycle, and document the parity delta against the old platform path. Do not broaden the slice into reusable template work. Verify with the app repo-local command and any required Lifeline verification before completion and report the exact files changed plus the parity gaps still open.

### Worker Prompt: Playbook Shadow Codification

Work only inside `repos/fawxzzy-playbook`.

Own the shadow codification slice for the Lifeline platform restart. Capture decisions, failure modes, migration checklist items, and reusable completion criteria derived from the current Lifeline work. Do not move execution ownership into Playbook and do not block on speculative future automation. Verify with the Playbook repo-local command before completion and report the exact files changed plus any doctrine gaps that still depend on fresh Lifeline evidence.

## Sequencing Rules

Use these sequencing rules at the stack root:

1. start Lifeline execution before asking Playbook to formalize everything
2. keep Atlas as coordinator only
3. prefer one agent per repo or non-overlapping owner-repo slice
4. do not let multiple workers edit the same repo root without explicit file-scope separation
5. do not widen to multi-service migration until the pilot milestone is evidenced

## Failure Modes To Avoid

- Atlas absorbs execution work and loses coordination clarity
- Playbook becomes a gate in front of still-unknown execution details
- success is framed as stack-wide replacement instead of one real pilot
- worker lanes overlap and generate merge noise instead of evidence
- root doctrine drifts into duplicating owner-repo implementation truth

## Decision Gate

Use this gate for every next step:

- if the work changes milestone framing, ownership, sequencing, or scoreboarding, it belongs at the stack root
- if the work changes platform behavior, deploy mechanics, pilot integration, or runbook mechanics, it belongs in the owner repo

## Status On 2026-04-21

Current stack-owned decision:

- continue from the recovered operating model rather than treating the restart as a blank slate
- keep the separation `atlas` -> coordinator, `lifeline` -> executor, `playbook` -> codifier
- treat Wave 1 as the active frontier
- use one real pilot as the proof milestone

This document is the explicit restart anchor for that posture.

Execution packet for the current wave:

- `docs/ops/ATLAS-LIFELINE-WAVE-1-LAUNCH.md`
