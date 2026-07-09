# AI Long-Run Batch Orchestration - Cross-Marker Ratchet Opportunity Contract Freeze - 2026-07-08

## Scope

This is a docs-only ATLAS-root contract freeze for a future `AI Long-Run Batch Orchestration` read-model helper.

It freezes the contract for identifying cross-marker ratchet opportunities. It does not implement the helper.

## Current basis

- Root branch: `main`
- Root basis: `4104dc9f`
- Current `AI Long-Run Batch Orchestration`: `69%`
- Current `Cortex Readiness`: `46%`
- Current `Playbook Everywhere + Cortex Interface`: `45%`
- Selected by: `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-CROSS-MARKER-RATCHET-EVIDENCE-NEXT-SLICE-SELECTION-2026-07-08.md`

## Contract definition

A cross-marker ratchet opportunity is a receipt-backed condition where one implemented proof cluster can legitimately satisfy ratchet criteria for more than one marker because those marker criteria depend on the same executed state change or proof-backed adoption widening.

The opportunity is advisory only. It may recommend review or future packet routing. It must not move markers, create final receipts, rewrite manifests, mutate owner repos, or decide release readiness.

## Motivating evidence

The motivating evidence is the Cortex second advisory substrate helper cluster:

- implementation: `ops/cortex/second_advisory_substrate_consumption.py`
- tests: `tests/test_cortex_second_advisory_substrate_consumption.py`
- Cortex reconciliation: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-08.md`
- Playbook/Cortex reconciliation: `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-SECOND-IMPLEMENTATION-BACKED-CONSUMER-CLASS-PROOF-RECONCILIATION-2026-07-08.md`

That cluster is admissible because the same implementation proof is cited by two separate marker receipts with distinct ratchet reasons:

- Cortex: a second advisory substrate consumer exists and is proven authority-false.
- Playbook/Cortex: a second implementation-backed consumer class exists and is proven distinct from the earlier classes.

## Admitted evidence

Future implementation may read only root-owned, committed, receipt-backed sources:

- `docs/ops/*.md` receipts
- `docs/memory/initiatives/continuity-manifest-*.json`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- output from `ops/atlas/marker_aware_next_packet_planner.py --json`
- output from `ops/atlas/marker_knockout_selector.py --format json`
- output from `ops/atlas/playbook_adoption_matrix.py --json --scope root`
- output from Cortex advisory helpers when invoked on root-owned sources
- stack validation output

All evidence must be local, committed, root-owned, and reproducible from the ATLAS checkout.

## Excluded evidence

Future implementation must reject or ignore:

- uncommitted local diffs as proof
- hidden chat transcripts
- stale PR body claims
- green CI without a receipt-backed ratchet reason
- owner-repo implementation truth unless explicitly cited by a root receipt
- Fitness, Mazer, Stripe, Vercel, BrowserStack, Supabase, deploy, release, or live-readiness state
- secrets or `.env*` values
- workflow-dispatch state as an action surface
- protected surfaces such as `archive/`, `.playwright-mcp/`, `.vercel/`, and `secrets/`
- marker movement claims not backed by committed marker receipts

## Marker adjacency model

The future helper may classify marker relationships as:

- `same_lane`: a proof belongs only to one marker lane.
- `supporting_lane`: a proof in one marker provides prerequisite support but does not itself satisfy another marker's ratchet condition.
- `adjacent_reuse_candidate`: a proof appears to satisfy more than one marker criterion and has separate receipt references for each claimed marker impact.
- `owner_lane_only`: the proof belongs to an owner repo or product lane and must not be pulled into ATLAS root marker movement by fallback.
- `excluded`: evidence is outside root-owned, receipt-backed authority.

The only valid cross-marker opportunity class is `adjacent_reuse_candidate`.

## Proof reuse model

Proof reuse is admissible only when all of these are true:

1. One concrete implementation or proof cluster is named.
2. At least two marker receipts cite that cluster.
3. Each marker receipt states a distinct ratchet reason.
4. The source marker criteria were already defined before or during the cited receipt chain.
5. The reused proof does not require extra owner mutation, secret handling, deploy, workflow dispatch, or protected-surface touch.
6. The reuse does not create a final receipt or marker write from inside the helper.
7. The helper output remains advisory and routes to a human/Codex packet for any actual ratchet.

## False-positive prevention

The future helper must fail closed when:

- a marker move is inferred only from wording similarity
- a receipt mentions a helper but does not cite implementation-backed proof
- a receipt is docs-only and no executed state changed
- an owner-repo proof is being used to move ATLAS root by fallback
- current marker values conflict across Book, manifest, and receipt surfaces
- one lane's support dependency is mistaken for another lane's ratchet clearance
- the same proof is double-counted inside one marker lane
- the proof requires unstated external state

## Future helper contract

Future implementation may be admitted as:

- `ops/atlas/cross_marker_ratchet_opportunity.py`
- `tests/test_atlas_cross_marker_ratchet_opportunity.py`

Expected command:

```text
python ops/atlas/cross_marker_ratchet_opportunity.py --json
```

Optional safe output:

```text
python ops/atlas/cross_marker_ratchet_opportunity.py --json --output tmp/cross-marker-ratchet/opportunities.json
```

Any output path must be under `tmp/**.json`.

## Expected JSON fields

The future helper must emit deterministic JSON with at least:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_commit`
- `source_receipts`
- `candidate_count`
- `opportunity_count`
- `opportunities`
- `opportunities[].opportunity_id`
- `opportunities[].primary_marker`
- `opportunities[].adjacent_markers`
- `opportunities[].shared_proof_cluster`
- `opportunities[].implementation_surfaces`
- `opportunities[].test_surfaces`
- `opportunities[].receipt_refs`
- `opportunities[].ratchet_reasons`
- `opportunities[].classification`
- `opportunities[].recommended_packet`
- `blocked_candidates`
- `authority_denials`
- `owner_lane_exclusions`
- `protected_surface_exclusions`
- `marker_write_authority=false`
- `final_receipt_authority=false`

## Authority denials

The future helper must deny:

- marker write authority
- final receipt authority
- owner-repo mutation
- Fitness work
- Mazer work
- Vercel mutation
- Supabase mutation
- BrowserStack proof execution
- Stripe live readiness
- deploy authority
- workflow edit or dispatch authority
- secret read or write authority
- protected-surface writes
- root package publication

## Proof matrix for future implementation

Future first implementation must prove:

- live root scan emits one opportunity for the Cortex second advisory substrate and Playbook/Cortex second consumer proof pair
- docs-only selector and contract-freeze receipts do not count as marker-ratchet opportunities
- owner-lane evidence is excluded
- protected paths are rejected
- uncommitted local diffs are not proof
- missing receipt references fail closed
- conflicting marker values fail closed or mark the candidate blocked
- output is deterministic
- optional output writes only under `tmp/**.json`
- helper never reports marker or final receipt authority

## Marker decision

No marker moves in this contract freeze.

- `AI Long-Run Batch Orchestration` remains `69%`
- `Cortex Readiness` remains `46%`
- `Playbook Everywhere + Cortex Interface` remains `45%`

This packet freezes a future advisory read-model contract. It does not implement the worker or clear a new blocker.

## Next exact packet

```text
CODEX-MSG-ID: CODEX-2026-07-08-AI-LONG-RUN-CROSS-MARKER-RATCHET-OPPORTUNITY-FIRST-IMPLEMENTATION-ADMISSION

Run a docs-only first-implementation admission for `ops/atlas/cross_marker_ratchet_opportunity.py` and `tests/test_atlas_cross_marker_ratchet_opportunity.py`.

Do not implement the worker yet.
Do not move markers.
Do not mutate owner repos.
```

