# AI Long-Run Batch Orchestration - Hour-Block Ratchet Wording False-Positive Fix - 2026-07-08

## Scope

This is a bounded ATLAS-root helper-fix receipt.

It fixes the hour-block queue path that falsely blocked the next safe `AI Long-Run Batch Orchestration` docs-only packet because the packet name contains `cross-marker ratchet`.

## Root cause

`ops/atlas/held_lane_prompt_suppression.py` previously used raw substring matching for protected authority terms. The selected packet:

```text
AI Long-Run Batch Orchestration cross-marker ratchet opportunity first-implementation admission
```

was planner-selected, classified as `docs_only_packet`, and marked `safe_to_select=true`, but suppression still blocked it because `cross-marker ratchet` matched the older `marker ratchet` protected term.

That confused marker-adjacent planning language with actual marker movement authority.

## Fix

The suppression helper now separates:

- selected packet source
- selected packet classification
- packet authority risk
- safe planner-selected docs-only or implementation-ready packets
- actual protected, owner-lane, stale, or marker-movement authority claims

The hour-block queue report now exposes the same distinction through:

- `selected_packet_source`
- `selected_packet_classification`
- `packet_authority_risk`

## Changed files

- `ops/atlas/held_lane_prompt_suppression.py`
- `ops/atlas/codex_hour_block_queue_prompt.py`
- `tests/test_atlas_held_lane_prompt_suppression.py`
- `tests/test_atlas_codex_hour_block_queue_prompt.py`

## Allowed examples

Allowed when explicitly planner-selected or operator-selected inside ATLAS root scope:

- docs-only packets containing `marker`, `ratchet`, or `movement` language
- first-implementation admission packets
- implementation-ready packets
- reconciliation packets
- prompt-pack or readiness packets

For the current live state, the expected safe packet is:

```text
AI Long-Run Batch Orchestration cross-marker ratchet opportunity first-implementation admission
```

It is allowed because it is planner-selected, classified as `docs_only_packet`, and has `packet_authority_risk=none`.

## Still blocked

The helper still blocks:

- unproven marker movement claims
- owner-lane fallback into Fitness, Mazer, or any owner repo
- secret access or mutation
- deploy, Vercel, Supabase, Stripe, BrowserStack, release-readiness, or platform authority
- workflow edits or workflow dispatch
- protected-surface touch
- stale or already completed packet reruns
- final receipt authority

## Verification

Focused tests:

```text
python -m unittest tests.test_atlas_held_lane_prompt_suppression -v
python -m unittest tests.test_atlas_codex_hour_block_queue_prompt -v
```

Live helper checks:

```text
python ops/atlas/marker_aware_next_packet_planner.py --json
python ops/atlas/codex_hour_block_queue_prompt.py --json
```

Full closeout validation must include:

```text
python -m unittest tests.test_atlas_held_lane_prompt_suppression -v
python -m unittest tests.test_atlas_codex_hour_block_queue_prompt -v
python -m unittest tests.test_atlas_marker_aware_next_packet_planner -v
python -m unittest tests.test_atlas_marker_knockout_selector tests.test_atlas_continuity_search tests.test_atlas_initiative_continuity_manifest_health -v
python ops/validation/validate_stack.py
```

## Marker decision

No marker moves from this helper fix.

- `AI Long-Run Batch Orchestration` remains `69%`
- `AI Repetition-to-Automation Pipeline` remains `54%`
- `Sandbox Simulation Readiness` remains `99%`
- `Cortex Readiness` remains `46%`
- `AI Work Session Stability & Auto-Sync Loop` remains `85%`
- `Playbook Everywhere + Cortex Interface` remains `45%`

## Owner-lane boundary

Fitness, Mazer, Playbook owner-repo work, deploys, secrets, workflow dispatch, and protected surfaces remain out of scope.

## Next exact packet

```text
AI Long-Run Batch Orchestration cross-marker ratchet opportunity first-implementation admission
```

That packet should now route through the hour-block helper without being blocked by marker/ratchet wording alone.
