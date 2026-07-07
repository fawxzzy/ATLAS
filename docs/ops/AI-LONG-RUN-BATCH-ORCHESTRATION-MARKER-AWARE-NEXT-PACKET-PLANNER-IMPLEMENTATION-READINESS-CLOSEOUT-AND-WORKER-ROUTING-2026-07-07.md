# AI Long-Run Batch Orchestration Marker-Aware Next-Packet Planner Implementation-Readiness Closeout And Worker Routing

Date: 2026-07-07
Status: implementation_ready
Scope: ATLAS root docs and governance only

## Objective

Close the remaining root-only readiness question for the marker-aware next-packet planner and freeze the exact bounded worker-routing result.

This packet does not implement the planner. It proves that the prior control-plane chain is complete enough to route one later implementation worker without widening into owner repos, workflow dispatch, secrets, deploy surfaces, protected surfaces, or marker movement.

## Source Chain

The readiness decision rests on this durable chain:

- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-AI-REPETITION-49-NEXT-SLICE-SELECTION-2026-07-07.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-MARKER-AWARE-NEXT-PACKET-PLANNER-CONTRACT-FREEZE-2026-07-07.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-MARKER-AWARE-NEXT-PACKET-PLANNER-FIRST-IMPLEMENTATION-ADMISSION-2026-07-07.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-MARKER-AWARE-NEXT-PACKET-PLANNER-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-07.md`

## Readiness Decision

The marker-aware next-packet planner is `implementation_ready`.

Why:

- the contract freeze selected the planner as the next root-only AI Long-Run control-plane helper;
- the first-implementation admission named the exact helper and test files;
- the prompt-pack froze the objective, candidate classes, JSON schema, admitted inputs, forbidden surfaces, forbidden authority, stop conditions, and proof matrix;
- the remaining gap is executed helper behavior plus tests, not root-side design ambiguity.

## Exact Worker-Routing Result

The exact next worker packet is:

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner first-implementation worker-cluster reconciliation
```

That worker may pursue exactly one objective:

```text
Implement one bounded, read-only marker-aware next-packet planner that consumes only admitted ATLAS-root read models and durable doctrine surfaces, emits deterministic JSON, classifies next-packet candidates, preserves owner-lane separation, denies authority-risk candidates, and proves the behavior through direct unit coverage.
```

## Exact Allowed Touch Surfaces

The worker may touch only:

- `ops/atlas/marker_aware_next_packet_planner.py`
- `tests/test_atlas_marker_aware_next_packet_planner.py`

If an output-file option is implemented, the helper may write only to an explicitly supplied safe `tmp/**` JSON path at runtime. That runtime output path is not a committed surface.

## Exact Required Helper Authority

The helper must remain read-only by default.

It may read or call only the admitted root-owned inputs from the prompt-pack:

- marker selector output;
- continuity manifest health;
- open-marker restart index;
- continuity coverage;
- AI work-session closeout;
- projection freshness;
- Playbook adoption matrix;
- reusable workflow proof-contract candidate output;
- Cortex authority-safe handoff and consumption output;
- ATLAS Book marker/current-state/restart surfaces;
- continuity manifests;
- Playbook doctrine notes and worker-orchestration standards.

## Exact Required Output

The helper must emit deterministic JSON with schema version:

```text
atlas.marker_aware_next_packet_planner.v1
```

The output must include:

- `schema_version`
- `status`
- `selected_marker`
- `selected_packet`
- `candidate_count`
- `candidate_scores`
- `held_lanes`
- `proof_gated_lanes`
- `owner_lane_boundaries`
- `playbook_rule_refs`
- `pattern_refs`
- `failure_mode_refs`
- `authority_risks`
- `rejected_candidates`
- `proof_requirements`
- `safe_to_continue`

Allowed status values:

- `ok`
- `advisory_recommendation`
- `blocked`
- `internal_error`

## Exact Required Candidate Classes

The helper must classify candidates into the frozen prompt-pack classes:

- `immediately_executable_packet`
- `held_lane`
- `proof_gated_lane`
- `owner_lane_blocked_lane`
- `external_proof_blocked_lane`
- `stale_packet`
- `implementation_ready_packet`
- `docs_only_packet`
- `unsafe_authority_risk_packet`
- `no_action_hold`

## Exact Forbidden Touch Surfaces

The worker must not touch:

- `repos/**`
- `secrets/**`
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- `.github/workflows/**`
- deployment outputs
- hidden transcript/session state
- owner repos, including Fitness and Mazer
- ATLAS Book, continuity manifests, receipt indexes, or generated root mirrors

## Exact Forbidden Authority

The worker must not:

- stage, commit, or push;
- mutate owner repos;
- touch Fitness or Mazer;
- touch secrets;
- deploy;
- dispatch workflows;
- approve or merge PRs;
- emit final receipts;
- move markers;
- infer proof from green CI alone;
- treat Cortex advisory output as authority;
- treat Playbook refs as execution authority.

## Exact Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_marker_aware_next_packet_planner -v`
2. `python ops/validation/validate_stack.py`
3. `git status --short`
4. `git diff --name-only`

The worker should also run any directly adjacent helper tests if importing shared logic exposes a new dependency.

## Exact Stop Conditions

Stop and return without implementation if the worker would require:

- owner repo mutation;
- Fitness or Mazer work;
- workflow dispatch or `.github/workflows/**` edits;
- secret, `.env*`, deploy, Vercel, Supabase, archive, or protected-surface touch;
- hidden transcript/session scraping;
- marker movement;
- final receipt authority;
- root mirror or manifest edits to make the helper pass;
- broad untracked backlog staging.

## Exact Post-Worker Package

If the worker lands cleanly, the exact next package is:

```text
AI Long-Run Batch Orchestration marker-aware next-packet planner first-implementation worker-cluster reconciliation
```

## Marker Decision

No marker moves from this readiness closeout.

- `AI Long-Run Batch Orchestration` remains `66%`.
- `AI Repetition-to-Automation Pipeline` remains `49%`.

## Rule

When the contract freeze, first-implementation admission, and prompt-pack already freeze a root-only planner's objective, files, inputs, output schema, proof matrix, and authority denials, route one bounded worker packet before adding more docs-only planner narration.

## Failure Mode

`Planner Readiness Drift`

If the lane keeps adding docs-only planner receipts after the prompt-pack and readiness closeout, it delays the real execution proof and risks turning packet selection into narration instead of implemented orchestration.
