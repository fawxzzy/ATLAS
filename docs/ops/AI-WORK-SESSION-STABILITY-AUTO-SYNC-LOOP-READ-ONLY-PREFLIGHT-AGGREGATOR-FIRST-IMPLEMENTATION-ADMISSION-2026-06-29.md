# AI Work Session Stability Auto-Sync Loop Read-Only Preflight Aggregator First-Implementation Admission

- Date: `2026-06-29`
- Lane: `AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator first-implementation admission`
- Mode: `docs-only root-bounded first-implementation admission`
- Scope: `freeze the first admitted read-only implementation slice, structured output contract, strict exit semantics, no-side-effects guard, and immediate worker-handoff boundary for ops/atlas/ai_work_session_preflight.py`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/memory/initiatives/continuity-manifest-ai-work-session-stability-auto-sync-loop.json`
  - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-CONTRACT-FREEZE-2026-06-29.md`
  - `ops/atlas/marker_knockout_selector.py`
  - `ops/atlas/continuity_manifest_health.py`
  - `ops/atlas/continuity_open_marker_restart_index.py`
  - `ops/atlas/continuity_coverage.py`
  - `ops/validation/validate_stack.py`
- Control-plane checkpoint: `codex/atlas-root-mazer-dirty-head-resync@ee82a10e`

## Objective

Freeze the smallest honest first implementation slice for a root-owned `ops/atlas/ai_work_session_preflight.py` command without implementing code, mutating owner repos, mutating platform state, refreshing projections automatically, or letting a preflight command quietly become a broader workflow orchestrator.

This pass does not:

- implement `ops/atlas/ai_work_session_preflight.py`
- implement `ops/atlas/ai_work_session_closeout.py`
- refresh `stack.lock.yaml`, inventory, Book mirrors, or runtime latest files from inside the future command
- stage files, commit, push, deploy, publish, or alter protected release-readiness outputs
- mutate owner repos, Supabase, Vercel, `secrets/`, `.env*`, `.playwright-mcp/`, `archive/`, or protected runtime surfaces
- clear the held Sandbox family or the current Fitness physical/manual proof blockers

## Inherited State

The opening contract already froze:

- the required manual AI-session start and close loop
- the authoritative, projected, and advisory source classes the loop must read
- the future tool family around preflight, closeout, projection freshness, component audit, and Playbook adoption
- the rule that the first executable must stay read-only and write nothing unless `--output` is supplied

Current control-plane truth for this admission is:

- the marker selector still holds `Sandbox Simulation Readiness` at `99%` and still routes this lane as the first honest downstream automation package after that held family
- initiative continuity health still reads `20 ok / 0 warning / 0 error`
- structured continuity coverage still reads `pending_review_count: 0`
- the seeded continuity substrate is broad enough that moving this lane above `0%` now widens eligible open-marker continuity from `6 / 6` to `7 / 7` once mirrors are refreshed
- pre-existing generated inventory writeback residue still exists in `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md`; this packet does not claim or consume that residue

## Exact First Admitted Implementation Slice

The first admitted implementation slice is limited to the following root-owned behaviors:

1. `one scope classifier`
   - classify the session as `atlas_root_governance`, `owner_repo`, `platform`, or `read_only_research`
   - fail closed when the requested surface cannot be classified from admitted inputs

2. `one read-only source collector`
   - read only already-existing authoritative, projected, and advisory surfaces
   - authoritative surfaces may include branch state, root git status, marker selector output, continuity health, restart indexes, release-readiness state, and current owner-head references
   - projected surfaces may include `stack.lock.yaml`, published inventory, Book mirrors, and restart projections
   - advisory surfaces may include Playbook adoption hints, provider-readiness hints, and protected-residue observations

3. `one source-class disagreement layer`
   - distinguish authoritative truth from projected drift and advisory hints
   - record disagreement without silently preferring a projection over an authoritative source
   - fail closed if admitted authoritative inputs are missing, malformed, or contradictory in ways that prevent evaluation

4. `one blocker and warning classifier`
   - classify only:
     - `ok`
     - `advisory_drift`
     - `blocker`
     - `internal_error`
   - keep blocker assignment bounded to already-admitted guard classes such as protected-surface risk, unavailable required proof surface, unresolved scope ownership, or contradictory authoritative inputs

5. `one machine-readable report renderer`
   - render one stable JSON payload only
   - print JSON to stdout by default
   - write JSON to disk only when `--output <relative-path>` is explicitly provided

6. `one strict-exit gate`
   - default mode: exit `0` for `ok` and `advisory_drift`, exit `2` for `blocker`, exit `3` for `internal_error`
   - `--strict`: exit `0` for `ok`, exit `1` for `advisory_drift`, exit `2` for `blocker`, exit `3` for `internal_error`
   - do not invent additional exit classes in the first slice

7. `one bounded output writer`
   - allow output only to one explicit ATLAS-root-relative file path
   - reject absolute paths
   - reject writes into protected surfaces such as `archive/`, `secrets/`, repo roots, `.env*`, `.playwright-mcp/`, or owner-repo trees

8. `one minimum proof harness`
   - prove only the admitted first slice
   - use fixtures, static snapshots, and bounded local proof inputs
   - do not widen into owner-repo mutation, platform mutation, or workflow execution proof

## Exact Structured Output Contract

The first slice must emit one JSON object with these top-level fields only:

- `status`
- `generated_at`
- `scope_class`
- `branch_state`
- `projection_freshness`
- `owner_repo_scope`
- `release_gates`
- `playbook_adoption`
- `protected_residue`
- `warnings`
- `blockers`
- `recommended_next_packet`

Field expectations:

- `status` is one of `ok`, `advisory_drift`, `blocker`, or `internal_error`
- `branch_state` summarizes active branch, parity posture, and dirty-state observations without mutating git state
- `projection_freshness` distinguishes authoritative-vs-projected agreement from projected drift
- `owner_repo_scope` lists only the bounded owner surfaces implicated by the current session
- `release_gates` reports only already-existing release or provider blockers; it does not infer clearance
- `playbook_adoption` reports adoption signals only; it does not mutate doctrine state
- `protected_residue` lists protected or intentionally preserved residue classes only
- `warnings` and `blockers` are arrays of bounded, machine-readable findings
- `recommended_next_packet` names one exact next packet or one exact hold result

The first slice may not:

- emit prose-only success output as the primary contract
- write auxiliary artifacts by default
- invent broader world-state summaries outside the admitted fields
- infer marker movement from report generation alone

## Exact No-Side-Effects Guard

The future implementation must carry this guard verbatim:

`No-side-effects guard: the read-only preflight aggregator may read admitted ATLAS-root, owner-head, release-readiness, continuity, marker, inventory, and doctrine surfaces; classify scope, drift, residue, warnings, and blockers; and render one bounded JSON report to stdout or one explicit root-relative output path, but it may not mutate git state, mutate owner repos, mutate platform state, refresh projections automatically, write runtime latest files by implication, stage files, commit, deploy, publish, or treat projected sources as authoritative truth.`

## Exact Deferred Later Slices

Deferred to later packets are:

- prompt-pack and worker handoff wording for the first code worker
- implementation-readiness closeout and worker-routing beyond this admission boundary
- the actual `ops/atlas/ai_work_session_preflight.py` implementation
- the closeout command, projection-freshness command, component-utilization audit, and Playbook adoption matrix
- reusable workflow wrapping and required-check enforcement
- any owner-repo or platform mutation-bearing follow-on

Deferred does not mean admitted now.

## Exact Next Package

`AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator prompt-pack and worker handoff contract`

Why:

- the first implementation slice, output contract, exit semantics, and no-side-effects guard are now explicit
- the next remaining docs-only ambiguity is the exact worker objective, proof matrix wording, allowed-touch surfaces, forbidden-touch surfaces, and stop conditions for the first implementation packet

## Ratchet Decision

Ratchet:

- `AI Work Session Stability & Auto-Sync Loop: 0% -> 10%`

Why:

- this pass materially clears the first implementation ambiguity by freezing the admitted first slice rather than only restating the contract
- the widened continuity substrate now honestly promotes this lane from an excluded `0%` supporting marker to a restart-ready eligible open marker
- the move stays conservative because no command implementation, no reusable workflow, and no enforced check has landed yet

## Validation Note

Live proof during this admission reads:

- `python .\ops\atlas\marker_knockout_selector.py --format json`
  - still holds `Sandbox Simulation Readiness`
  - now routes this lane at `10%`
  - now names `AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator prompt-pack and worker handoff contract` as the next exact package
- `python .\ops\atlas\continuity_manifest_health.py`
  - `20 ok / 0 warning / 0 error`
- `python .\ops\atlas\continuity_open_marker_restart_index.py`
  - `7 / 7` eligible open markers restart-ready
- `python .\ops\atlas\continuity_coverage.py`
  - `status: structured`
  - `pending_review_count: 0`
- `python .\ops\validation\validate_stack.py`
  - `critical=0 error=1 warning=3 info=0`
  - the single error is pre-existing `runtime/cortex/catalog/memory/working-memory.latest.json` drift, which remains outside this admitted lane

## Rule

`Structured Output Before Enforcement`

A session-safety preflight lane must not be treated as implementation-ready until its first machine-readable report contract and strict exit semantics are explicit enough to support future reuse and branch protection without hidden side effects.

## Pattern

contract freeze -> first-implementation admission -> prompt-pack and worker handoff -> implementation-readiness closeout -> bounded worker landing -> proof-backed widening

## Failure Mode

`Preflight Trust Collapse`

The lane fails if a so-called preflight command quietly edits projections, writes runtime latest files by implication, collapses authoritative and projected truth into one undifferentiated read, or emits unstable prose that cannot later become a repeatable governance signal.
