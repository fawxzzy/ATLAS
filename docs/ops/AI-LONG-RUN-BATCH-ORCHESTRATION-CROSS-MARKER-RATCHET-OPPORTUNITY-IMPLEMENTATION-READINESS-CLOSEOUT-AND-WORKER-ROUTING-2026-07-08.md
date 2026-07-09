# AI Long-Run Batch Orchestration Cross-Marker Ratchet Opportunity Implementation-Readiness Closeout And Worker Routing

Date: 2026-07-08
Status: implementation_ready
Scope: ATLAS root docs and governance only

## Objective

Close the remaining root-only readiness question for the cross-marker ratchet opportunity helper and freeze the exact bounded worker-routing result.

This packet does not implement the helper. It proves that the prior control-plane chain is complete enough to route one later implementation worker without widening into owner repos, workflow dispatch, secrets, deploy surfaces, protected surfaces, final receipt authority, or marker movement.

## Source Chain

The readiness decision rests on this durable chain:

- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-CROSS-MARKER-RATCHET-EVIDENCE-NEXT-SLICE-SELECTION-2026-07-08.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-CONTRACT-FREEZE-2026-07-08.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-08.md`
- `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-08.md`

## Readiness Decision

The cross-marker ratchet opportunity helper is `implementation_ready`.

Why:

- the selector selected the cross-marker opportunity contract after one Cortex proof also satisfied Playbook/Cortex second-consumer criteria;
- the contract freeze defined the advisory helper boundary for proof reuse;
- the first-implementation admission named the exact helper and test files;
- the prompt-pack froze the worker objective, command, output schema, opportunity records, blocked-candidate records, proof obligations, allowed inputs, forbidden surfaces, forbidden authority, and stop conditions;
- the remaining gap is executed helper behavior plus tests, not root-side design ambiguity.

## Exact Worker-Routing Result

The exact next worker packet is:

```text
AI Long-Run Batch Orchestration cross-marker ratchet opportunity first-implementation worker-cluster reconciliation
```

That worker may pursue exactly one objective:

```text
Implement one bounded, read-only cross-marker ratchet opportunity helper that consumes only admitted ATLAS-root read models and durable receipt/manifest surfaces, emits deterministic advisory JSON, reports proof-reuse opportunities and blocked candidates, preserves owner-lane separation, denies authority-risk candidates, and proves the behavior through direct unit coverage.
```

## Exact Allowed Touch Surfaces

The worker may touch only:

- `ops/atlas/cross_marker_ratchet_opportunity.py`
- `tests/test_atlas_cross_marker_ratchet_opportunity.py`

If an output-file option is implemented, the helper may write only to an explicitly supplied safe `tmp/**` JSON path at runtime. That runtime output path is not a committed surface.

## Exact Required Helper Authority

The helper must remain read-only by default.

It may read or call only the admitted root-owned inputs from the prompt-pack:

- continuity manifests;
- ATLAS Book marker/current-state/restart/receipt-index surfaces;
- committed `docs/ops/*.md` receipts;
- marker-aware next-packet planner output;
- continuity manifest health;
- open-marker restart index;
- continuity coverage.

## Exact Required Output

The helper must emit deterministic JSON with schema version:

```text
atlas.cross_marker_ratchet_opportunity.v1
```

The output must include:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_commit`
- `source_receipts`
- `candidate_count`
- `opportunity_count`
- `opportunities`
- `blocked_candidates`
- `authority_denials`
- `owner_lane_exclusions`
- `protected_surface_exclusions`
- `marker_write_authority`
- `final_receipt_authority`

Allowed status values:

- `ok`
- `no_opportunities`
- `blocked`
- `internal_error`

Required authority values:

- `marker_write_authority`: `false`
- `final_receipt_authority`: `false`

## Exact Required Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_cross_marker_ratchet_opportunity -v`
2. `python -m unittest tests.test_atlas_marker_aware_next_packet_planner tests.test_atlas_codex_hour_block_queue_prompt tests.test_atlas_initiative_continuity_manifest_health tests.test_atlas_continuity_manifest -v`
3. `python ops/validation/validate_stack.py`
4. `python ops/atlas/cross_marker_ratchet_opportunity.py --json`
5. `git status --short`
6. `git diff --name-only`

## Exact Forbidden Touch Surfaces

The worker must not touch:

- `repos/**`
- Fitness owner repo files
- Mazer owner repo files
- Playbook owner repo files
- `secrets/**`
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- `.github/workflows/**`
- deployment outputs
- hidden transcript/session state
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
- treat Cortex advisory output as execution authority;
- treat Playbook refs as owner-truth authority.

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
AI Long-Run Batch Orchestration cross-marker ratchet opportunity first-implementation worker-cluster reconciliation
```

That reconciliation may add one bounded reconciliation receipt and exact Book/manifest mirrors only after focused proof, adjacent regression proof, live helper output, and stack validation pass.

## Marker Decision

No marker moves from this readiness closeout.

- `AI Long-Run Batch Orchestration` remains `69%`.
- `Cortex Readiness` remains `46%`.
- `Playbook Everywhere + Cortex Interface` remains `45%`.

## Rule

When the selector, contract freeze, first-implementation admission, and prompt-pack already freeze a root-only helper's objective, files, inputs, output schema, proof matrix, and authority denials, route one bounded worker packet before adding more docs-only helper narration.

## Failure Mode

`Cross-Marker Readiness Drift`

If the lane keeps adding docs-only cross-marker receipts after the prompt-pack and readiness closeout, it delays real execution proof and risks turning cross-marker proof reuse into narration instead of implemented orchestration.
