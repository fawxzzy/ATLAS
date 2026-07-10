# AI Long-Run Batch Orchestration Autonomous Lane Scheduler Contract Freeze - 2026-07-10

## Purpose

Freeze the deterministic one-packet ATLAS autonomous lane scheduler contract before or alongside the first implementation slice.

## Objective

Build one root-owned controller that:

1. reads root-owned ATLAS state only
2. selects exactly one safe next packet per invocation
3. requires an explicit reselection receipt when it bypasses the held Sandbox lane
4. renders one Codex execution prompt
5. stops cleanly when no safe packet exists

## Exact Input Surfaces

The scheduler may consume:

- `ops/atlas/ai_work_session_preflight.py`
- `ops/atlas/marker_knockout_selector.py`
- `ops/atlas/marker_aware_next_packet_planner.py`
- `ops/atlas/held_lane_prompt_suppression.py`
- continuity helpers and manifests already admitted under `ops/atlas/**`
- current git branch/head/parity state
- one operator work program under `tmp/atlas/**.json`

The scheduler may not consume:

- owner-repo source trees
- hidden transcript or chat state
- secrets or env values
- Vercel or Supabase live data
- deploy logs or browser profiles

## Deterministic Precedence Model

The frozen decision precedence is:

1. `validation_cleanup`
2. `worker_reconciliation`
3. `routed_worker`
4. `exact_manifest_packet`
5. `operator_program_packet`
6. `cross_marker_opportunity`
7. `planner_candidate`
8. `hold`

## Operator Work Program

The scheduler consumes one local program with schema:

- `atlas.autonomous-work-program.v1`

The program governs:

- allowed markers
- excluded markers
- forbidden owner lanes
- docs-only streak limit
- reselection permission
- phase priority
- hard-stop classes

## Reselection Requirement

When the current lane is held and the scheduler selects another marker from the allowed program:

- `requires_reselection_receipt: true`
- exact receipt path must be emitted
- previous routing must stay visible
- selected routing must stay visible
- markers remain unchanged by the scheduler itself

## Candidate Model

Every candidate must expose:

- marker
- lane
- packet
- phase
- score
- source
- proof delta
- blocked reason
- stale reason
- file-overlap risk
- external-input requirement
- reselection requirement
- safe / unsafe state

## Output Contract

Top-level fields are frozen as:

- `schema_version`
- `status`
- `decision`
- `routing_mode`
- `selected_marker`
- `selected_lane`
- `selected_packet`
- `packet_phase`
- `selected_packet_source`
- `requires_reselection_receipt`
- `reselection_receipt`
- `candidate_count`
- `candidates`
- `skipped_candidates`
- `blocked_candidates`
- `validation_state`
- `git_state`
- `scope_lock`
- `authority_denials`
- `safe_to_execute`
- `stop_reason`
- `prompt_output`
- `next_recommended_command`

Status classes are frozen as:

- `execute`
- `hold`
- `validation_cleanup`
- `blocked`
- `internal_error`

## Prompt Rendering

The generated prompt must:

- name exactly one selected packet when executable
- name the exact phase
- include branch/head and required preflight
- preserve the root scope lock
- include the reselection bundle when required
- stop with `ATLAS ROOT HELD - NO SAFE AUTOCOMPLETE PACKET` when no safe packet exists

## Exact Implementation Files

The first implementation slice is admitted to touch only:

- `ops/atlas/autonomous_lane_scheduler.py`
- `tests/test_atlas_autonomous_lane_scheduler.py`
- `ops/atlas/codex_hour_block_queue_prompt.py`
- `tests/test_atlas_codex_hour_block_queue_prompt.py`

## Reconciliation Requirement

After implementation, reconcile through:

- `AI Long-Run Batch Orchestration autonomous lane scheduler first-implementation worker-cluster reconciliation`

The reconciliation must record:

- decision precedence
- operator program behavior
- reselection behavior
- prompt generation behavior
- focused tests
- validation proof
- no owner-repo mutation
- no secret, deploy, workflow, or platform mutation

## Marker Decision

No marker moves from this contract freeze.

