# Cortex Readiness Second Advisory Substrate Consumption Prompt-Pack And Worker Handoff Contract - 2026-07-08

- CODEX-MSG-ID: `CODEX-2026-07-08-CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-PROMPT-PACK`
- Date: `2026-07-08`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `prepare the future Cortex-side second advisory substrate consumer without implementing it`
- Admission basis: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-08.md`
- Branch basis: `main@420463ed457af3553e6246282f0ed17ec5ab4795`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Freeze the worker handoff contract for the admitted second Cortex advisory substrate consumer:

- future implementation file: `ops/cortex/second_advisory_substrate_consumption.py`
- future test file: `tests/test_cortex_second_advisory_substrate_consumption.py`

This packet does not implement either file.

## Worker Objective

Implement a read-only Cortex-side helper that consumes one explicit root-relative advisory substrate source, validates that it is inside an admitted source class, summarizes it as advisory-only context, preserves authority denials, and emits deterministic JSON without gaining execution, approval, owner-truth, deploy, secret, workflow-dispatch, owner-repo mutation, protected-surface mutation, final-receipt, or marker authority.

## Future CLI Contract

Expected command forms:

- `python ops/cortex/second_advisory_substrate_consumption.py`
- `python ops/cortex/second_advisory_substrate_consumption.py --json`
- `python ops/cortex/second_advisory_substrate_consumption.py --source <root-relative-path>`
- `python ops/cortex/second_advisory_substrate_consumption.py --output <root-relative-path>`
- `python ops/cortex/second_advisory_substrate_consumption.py --strict`

Expected JSON fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_ref`
- `source_digest`
- `substrate_class`
- `consumption_result`
- `preserved_authority_denials`
- `advisory_payload`
- `forbidden_surfaces`
- `warnings`
- `blockers`
- `safe_to_use`

Expected status classes:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## Implementation Plan For Future Worker

1. Add `ops/cortex/second_advisory_substrate_consumption.py`.
2. Add `tests/test_cortex_second_advisory_substrate_consumption.py`.
3. Parse `--json`, `--source`, `--output`, and `--strict`.
4. Require `--source` for actual payload consumption; default mode may report the contract surface without writing.
5. Reject absolute paths, parent traversal, protected paths, owner repo paths, secret paths, deploy paths, final-receipt paths, and hidden transcript/session refs.
6. Classify the source into one admitted substrate class from the contract freeze.
7. Validate source shape according to that substrate class.
8. Compute `source_digest` deterministically.
9. Preserve the full authority-denial set in the output.
10. Emit advisory output only.
11. Default to stdout/no writes.
12. Permit writes only when `--output` is explicit and under `tmp/**`.
13. Return nonzero in `--strict` when blockers or unsafe status exist.

## Allowed Future Files

- `ops/cortex/second_advisory_substrate_consumption.py`
- `tests/test_cortex_second_advisory_substrate_consumption.py`
- one implementation-backed reconciliation receipt under `docs/ops/**` after proof passes
- exact ATLAS Book and manifest mirrors only if implementation-backed truth changes

## Forbidden Future Surfaces

- `repos/**`
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- deployment outputs
- owner-repo receipts as truth inputs
- final Lifeline receipts
- hidden transcript, chat, or session state
- runtime latest files by default
- ATLAS Book, receipt index, selector, or manifest mutation by default
- workflow dispatch or workflow edits

## Required Future Proof

Future verification must include:

- `python -m unittest tests.test_cortex_second_advisory_substrate_consumption -v`
- `python -m unittest tests.test_cortex_authority_safe_interface_handoff tests.test_cortex_authority_safe_handoff_consumption tests.test_cortex_worker_prompt tests.test_cortex_worker_plan tests.test_cortex_stack_consumption_pilot tests.test_cortex_stack_handoff -v`
- `python -m unittest tests.test_atlas_held_lane_prompt_suppression tests.test_atlas_codex_hour_block_queue_prompt -v`
- `python -m unittest tests.test_atlas_marker_knockout_selector tests.test_atlas_continuity_search tests.test_atlas_initiative_continuity_manifest_health -v`
- `python ops/validation/validate_stack.py`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python ops/atlas/codex_hour_block_queue_prompt.py --json`
- `python ops/atlas/held_lane_prompt_suppression.py --json`

Required proof outcomes:

- validation has `critical=0 error=0`
- default helper run writes no files
- valid second advisory substrate returns `status=ok` and `safe_to_use=true`
- malformed source fails closed
- owner-repo, Fitness, and Mazer source refs are rejected
- hidden transcript refs are rejected
- deploy, platform, and secret paths are rejected
- absolute source and output paths are rejected
- protected source and output paths are rejected
- allowed `tmp/**` output works only with explicit `--output`
- deterministic JSON field ordering is stable
- all authority denials are preserved
- no owner repo is touched
- no protected surface is touched
- no marker movement is claimed until implementation-backed proof lands

## Prompt Pack For Future Codex Worker

```text
CODEX-MSG-ID: CODEX-2026-07-08-CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-WORKER-CLUSTER

Objective:
Implement the Cortex-side second advisory substrate consumption helper admitted by:
- docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-08.md
- docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-08.md

Allowed files:
- ops/cortex/second_advisory_substrate_consumption.py
- tests/test_cortex_second_advisory_substrate_consumption.py
- exact implementation-backed reconciliation receipt after tests pass
- exact ATLAS Book and manifest mirrors only if implementation-backed truth changes

Hard boundaries:
- do not mutate repos/**
- do not touch Fitness, Mazer, Playbook owner repo, or any owner repo
- do not touch Supabase, Vercel, deploy, secrets, .env*, .vercel, .playwright-mcp, archive, or final receipt surfaces
- do not dispatch workflows or _stack
- do not scrape hidden transcript, chat, or session state
- do not grant Cortex execution, approval, owner-truth, deploy, secret, transcript-scraping, automatic _stack dispatch, repo mutation, platform mutation, protected-surface mutation, marker movement, or final-receipt authority

Implementation:
- build a read-only report helper with --json, --source, --output, and --strict
- reject absolute, parent-traversal, protected, owner-repo, final-receipt, secret, deploy, and hidden transcript paths
- default to stdout/no writes
- write only when --output is explicit and under tmp/**
- use deterministic JSON ordering
- classify source refs into admitted second advisory substrate classes
- validate the consumed source shape
- compute source_digest deterministically
- preserve every authority denial
- set safe_to_use=false when the source is unsafe, malformed, disallowed, missing required fields, or validation has critical/error counts

Verification:
- run the test and validation commands listed in the prompt-pack receipt
- commit only if validation has critical=0 error=0 and only admitted files are staged
```

## Marker Decision

No marker moves.

- `Cortex Readiness` remains `45%`.
- `Sandbox Simulation Readiness` remains `99%`.
- `AI Repetition-to-Automation Pipeline` remains `54%`.
- `AI Long-Run Batch Orchestration` remains `69%`.
- `AI Work Session Stability & Auto-Sync Loop` remains `85%`.
- `Playbook Everywhere + Cortex Interface` remains `40%`.

## Exact Next Packet

`Cortex Readiness second advisory substrate consumption implementation-readiness closeout and worker routing`

## Boundaries Preserved

- Fitness was not mutated.
- Mazer was not mutated.
- Playbook owner repo was not mutated.
- No owner repo was mutated.
- Supabase was not touched.
- Vercel was not touched.
- Deployment was not touched.
- Secrets and `.env*` files were not touched.
- Protected surfaces were not touched.
- Cortex remains read-only advisory.
