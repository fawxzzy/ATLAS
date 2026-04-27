# Cortex MVP Spec

- Status: Draft
- Date: 2026-04-26
- Canonical boundary reference: [ADR: Canonical AI Naming and Cortex Boundary](../decisions/adr-canonical-ai-naming-and-cortex-boundary.md)

## Purpose

Cortex is the root-owned AI umbrella for ATLAS. The MVP is not a general autonomous agent and not a second truth store. It is a project intelligence engine that reads explicit stack state, assembles compact context, proposes bounded worker plans, interprets proof, and writes auditable receipts.

This spec defines the first usable Cortex slice while preserving the current root policy:

- ATLAS owns stack policy and root coordination.
- Cortex owns AI interpretation, observation, context, and proof intelligence.
- Fitness owns product UI truth.
- Playbook owns governance truth.
- `_stack` owns orchestration and enforcement.
- Lifeline owns receipts and approval truth.

## Scope

The MVP covers the smallest Cortex surface that makes the stack more legible and safer to operate.

In scope:

- reading current rail state from explicit files and runtime artifacts
- assembling compact context packets for bounded work
- planning PR-sized worker lanes
- interpreting verification output into done, blocked, or needs-follow-up states
- writing receipt-style summaries that can be consumed by Lifeline-owned flows
- optionally reserving `Cortex Link` later as a connector sublayer if a real connector surface emerges

Out of scope:

- product implementation truth
- governance policy authoring
- execution authority over repos
- hidden memory or transcript-only state
- automatic mutation of repos
- broad stack cleanup unrelated to the active Cortex rail

## Non-Goals

Cortex MVP is not trying to become:

- a general AGI layer
- a repo editor
- a hidden daemon
- a replacement for Playbook, `_stack`, Lifeline, or Fitness
- a global knowledge base that silently overrides repo-owned truth
- a broad consolidation pass for stale stack debt

If a behavior requires owner truth outside Cortex, Cortex must route by reference rather than absorb the ownership boundary.

## Core Capabilities

### Rail State Reader

Purpose: identify the latest clean step and the next correct layer for the current ATLAS posture.

Reads from explicit sources such as:

- `stack.yaml`
- `README-STACK.md`
- stack policy and architecture docs under `docs/`
- Cortex runtime artifacts under `runtime/cortex/**`
- session and worker receipts under the root runtime lanes

Output:

- current rail name
- latest clean step
- active dirty lanes
- next recommended layer
- relevant boundary reminders

### Context Assembler

Purpose: build small, deterministic context packets instead of relying on transcript residue.

Inputs may include:

- stack manifest data
- runtime artifacts
- proof maps
- handoff summaries
- git status or other explicit workspace signals

Output:

- a compact worker context packet
- a minimal evidence list
- a normalized task frame with only the fields needed for execution

### Worker Planner

Purpose: split work into bounded, PR-sized lanes that a worker can execute safely.

Planner behavior:

- keep scope small
- prefer one objective per lane
- preserve owner boundaries
- flag when work crosses Fitness, Playbook, `_stack`, or Lifeline truth
- generate worker prompts that are explicit about inputs, outputs, and verification

Output:

- lane plan
- dependency order
- scope guardrails
- worker prompt draft

### Proof Interpreter

Purpose: turn validation output into an auditable status judgment.

Inputs:

- test output
- verification output
- visual or semantic proof summaries
- worker receipts

Output:

- `done`
- `blocked`
- `needs-follow-up`
- short reason
- evidence pointers

This layer should explain why an outcome was classified, not just label it.

### Receipt Writer

Purpose: emit a concise proof summary that can be attached to Lifeline-owned receipt flows.

Output shape:

- what was attempted
- what was verified
- what remains open
- what evidence backs the conclusion
- what owner should consume the result next

Receipts from Cortex are advisory proof summaries. They do not replace Lifeline receipt semantics.

### Optional Cortex Link Later

`Cortex Link` stays reserved. If a real connector surface emerges later, it may hold:

- GitHub connector surface
- Vercel connector surface
- local repo adapter
- document or artifact readers
- standardized evidence links

That layer is optional and deferred until the connector surface is concrete enough to justify the name.

## Inputs and Outputs

### Primary Inputs

- `git status`
- stack manifest and registry data
- relevant `runtime/cortex/**` artifacts
- explicit handoff summaries
- validation output
- proof maps and receipts

### Primary Outputs

- rail state summaries
- compact context packets
- PR-sized worker plans
- proof classifications
- receipt summaries
- optional connector references

### Output Constraints

- outputs must be explicit files or explicit artifacts
- outputs must be reproducible from the same inputs
- outputs must not depend on hidden local memory
- outputs must not claim owner truth outside Cortex

## Boundary Rules

These rules preserve the current accepted boundary.

- Fitness owns product UI truth, so Cortex may observe Fitness state but may not redefine Fitness behavior.
- Playbook owns governance, so Cortex may summarize governance but may not author or override governance truth.
- `_stack` owns orchestration and enforcement, so Cortex may recommend sequencing but may not enforce completion.
- Lifeline owns receipts and approval semantics, so Cortex may draft proof summaries but may not replace receipt authority.
- ATLAS root owns stack policy and routing, so Cortex must stay inside the root contract and path policy.

Concrete rule:

- Cortex observes, interprets, and proves.
- Cortex does not own product truth, governance truth, approval truth, or enforcement truth.

## Runtime Surface

The active Cortex runtime surface remains under `runtime/cortex/**`.

The MVP should treat that surface as the root-owned working area for Cortex catalogs, context, supervisor outputs, and related artifacts. It should not treat `repos/cortex` as the active owner surface.

## Kernel v0.1 Primitives

Wave 1 adds three explicit, descriptive Cortex kernel artifacts:

- `runtime/cortex/kernel.state-model.seed.v1.json`
- `runtime/cortex/kernel.rule-registry.seed.v1.json`
- `runtime/cortex/kernel.proof-summary.examples.v1.json`

These artifacts are loaded by `ops/cortex/kernel.py`. They are data-only seed surfaces for the MVP and do not grant Cortex new mutation authority.

The kernel primitives are:

- `CortexPosture` for current owner/project posture and the current pivot classification
- `RailState` for the latest clean step, dirty lanes, verification state, and the next recommended move
- `CleanStep` for the latest proved rail milestone
- `DirtyLane` for open work that keeps the rail from being clean
- `VerificationResult` for normalized pass, fail, and known-debt summaries
- `NextAction` for the smallest bounded action Cortex should recommend next
- `CortexRuleRecord` for reusable rule, pattern, and failure-mode records
- `CortexProofSummary` for receipt-ready proof inputs

Proof summary rule:

- `passed` means the verification lane cleared without debt or blockers
- `completed_with_known_debt` means validation completed, but existing pre-tranche debt remains
- `failed` means the active tranche introduced or exposed a blocking failure

This distinction matters because Cortex must not treat unchanged stack validation debt as a fresh regression.

## Phased Rollout

### Phase 0: Controlled Pivot

- finish the smallest clean catch-up needed to keep the current proof rail honest
- freeze new work that does not support Cortex MVP discovery
- do not widen scope into unrelated cleanup

### Phase 1: Cortex MVP Spec and Inventory

Target outcome:

- a clear inventory of the existing runtime/cortex surface
- a stable definition of Cortex MVP inputs and outputs
- a single spec that records the boundary and the non-goals

### Phase 2: Cortex Kernel v0.1

Target outcome:

- rail state parser
- current posture summarizer
- next-action recommender
- worker prompt generator

This phase should still be deterministic and bounded. It should not attempt autonomy.

### Phase 3: Proof and Memory Layer

Target outcome:

- proof result classifier
- normalized semantic and visual proof summaries
- memory packet format
- latest-clean-step ledger
- blocked-lane registry

The purpose of this phase is durable project memory, not hidden general memory.

### Phase 4: Cortex Link, if Needed

Target outcome:

- only if a real connector surface exists
- connector adapters for explicit external surfaces
- standardized evidence links

Do not create Link branding before the connector layer is real.

### Phase 5: Human-Approved Action Loop

Target outcome:

- Cortex proposes bounded work
- a worker executes within scope
- Cortex reads verification
- Lifeline records the receipt
- `_stack` and Playbook continue to enforce their own boundaries

This is the point where Cortex becomes a practical operating partner without becoming the authority.

## Failure Modes

The MVP should explicitly guard against these failures:

- turning Cortex into a second source of stack truth
- broad repo cleanup disguised as AI progress
- using transcript memory instead of explicit artifact inputs
- claiming completion without a proof artifact
- blurring Fitness, Playbook, `_stack`, or Lifeline ownership
- naming Link as a general umbrella before it has a real connector surface
- making Cortex mutate repos by default
- letting context packets grow into unreadable dumps

If a failure mode appears, the default response is to reduce scope and re-anchor on explicit files, explicit artifacts, and owner boundaries.

## Success Criteria

Cortex MVP is successful when it can reliably:

- tell the current rail state from explicit stack artifacts
- assemble a compact worker-ready context packet
- propose a bounded plan that respects ownership boundaries
- interpret verification output into a small set of stable outcomes
- write a concise receipt summary that Lifeline can consume

At that point Cortex is useful as a project intelligence engine even before any connector layer exists.
