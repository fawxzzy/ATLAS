# Cortex Simulation Substrate Readiness ATLAS Receipt Replay Prompt-Pack And Worker Handoff Contract

- Date: `2026-07-14`
- Opening checkpoint: `main@368d6820`
- Marker movement: none

## Worker Objective

Implement deterministic, digest-bound, chronological, advisory-only replay for `atlas.receipt.v1` and `atlas.execution-receipt.v2`, prove the mixed-source canary, and reconcile the 50% threshold only when every gate passes.

## Allowed Implementation

- `schemas/atlas.cortex.simulation.receipt-replay-manifest.v1.json`
- `schemas/atlas.cortex.simulation.receipt-replay.v1.json`
- `ops/cortex/receipt_replay.py`
- `tests/test_cortex_receipt_replay.py`
- `data/cortex/simulation-replays/first-mixed-replay/**.json`
- one implementation reconciliation receipt
- exact Book, registry, continuity, selector, and marker projections

## Worker Command

```text
python ops/cortex/receipt_replay.py --json --manifest data/cortex/simulation-replays/first-mixed-replay/manifest.json --output tmp/atlas/cortex-simulation-first-mixed-replay.json --strict
```

## Required Verification

```text
python -m unittest tests.test_cortex_receipt_replay tests.test_cortex_read_only_scenario_helper tests.test_cortex_simulation_agent_state_schema tests.test_cortex_simulation_substrate_requirements -v
python -m unittest tests.test_atlas_marker_knockout_selector tests.test_atlas_initiative_continuity_manifest_health -v
python ops/atlas/continuity_manifest_health.py
python ops/atlas/continuity_open_marker_manifest_coverage.py
python ops/cortex/index_working_memory.py
python ops/validation/validate_stack.py
git diff --check
```

## Stop Conditions

Stop the implementation cluster without marker movement when:

- any source digest, schema, chronology, duplicate-ID, trust, or path check fails
- only `contract_fixture` evidence participates
- output gains execution or external mutation authority
- any owner, `_stack`, platform, Discord, board, deploy, secret, model, browser, network, or subprocess surface changes
- focused, selector, continuity, catalog, or stack validation fails

## Return Contract

Return the implementation commit, exact canary status, receipt contracts and trust classes observed, transition counts, threshold eligibility, test counts, stack validation counts, denied actions, blockers, and next packet.

No prompt body may widen the frozen contract or implementation admission.
