# Cortex Readiness Authority-Safe Handoff Consumption Proof Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-06-CORTEX-READINESS-AUTHORITY-SAFE-HANDOFF-CONSUMPTION-PROMPT-PACK`
- Date: `2026-07-06`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `prepare the future Cortex-side handoff consumption proof worker without implementing it`
- Admission basis: `docs/ops/CORTEX-READINESS-AUTHORITY-SAFE-HANDOFF-CONSUMPTION-PROOF-FIRST-IMPLEMENTATION-ADMISSION-2026-07-06.md`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Freeze the worker handoff contract for the admitted Cortex-side consumer proof:

- future implementation file: `ops/cortex/authority_safe_handoff_consumption.py`
- future test file: `tests/test_cortex_authority_safe_handoff_consumption.py`

This packet does not implement either file.

## Worker Objective

Implement a read-only Cortex-side proof helper that consumes an explicit handoff JSON payload from `ops/cortex/authority_safe_interface_handoff.py`, validates the schema, verifies authority denials, and emits only advisory consumption output.

## Future CLI Contract

Expected command forms:

- `python ops/cortex/authority_safe_handoff_consumption.py`
- `python ops/cortex/authority_safe_handoff_consumption.py --json`
- `python ops/cortex/authority_safe_handoff_consumption.py --handoff <root-relative-path>`
- `python ops/cortex/authority_safe_handoff_consumption.py --output <root-relative-path>`
- `python ops/cortex/authority_safe_handoff_consumption.py --strict`

Expected JSON fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `handoff_ref`
- `handoff_digest`
- `consumption_result`
- `consumed_authority_denials`
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

1. Add `ops/cortex/authority_safe_handoff_consumption.py`.
2. Add `tests/test_cortex_authority_safe_handoff_consumption.py`.
3. Parse `--json`, `--handoff`, `--output`, and `--strict`.
4. Require `--handoff` for actual payload consumption.
5. Reject absolute paths, parent traversal, protected paths, owner repo paths, secret paths, deploy paths, and final-receipt paths.
6. Load only the explicit root-relative handoff JSON payload.
7. Validate the source handoff schema and status.
8. Compute `handoff_digest` deterministically.
9. Preserve every consumed authority denial in the output.
10. Emit advisory output only.
11. Default to stdout/no writes.
12. Permit writes only when `--output` is explicit and allowed.
13. Return nonzero in `--strict` when blockers or unsafe status exist.

## Allowed Future Files

- `ops/cortex/authority_safe_handoff_consumption.py`
- `tests/test_cortex_authority_safe_handoff_consumption.py`
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
- owner-repo receipts
- final Lifeline receipts
- runtime latest files by default
- ATLAS Book, receipt index, selector, or manifest mutation by default

## Required Future Proof

Future verification must include:

- `python -m unittest tests.test_cortex_authority_safe_handoff_consumption -v`
- `python -m unittest tests.test_cortex_authority_safe_interface_handoff tests.test_cortex_worker_prompt tests.test_cortex_worker_plan tests.test_cortex_stack_consumption_pilot tests.test_cortex_stack_handoff -v`
- `python -m unittest tests.test_atlas_ai_work_session_preflight tests.test_atlas_ai_work_session_closeout tests.test_atlas_projection_freshness tests.test_atlas_playbook_adoption_matrix -v`
- `python ops/validation/validate_stack.py`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python ops/atlas/ai_work_session_closeout.py --json --scope root`

Required proof outcomes:

- validation has `critical=0 error=0`
- default helper run writes no files
- allowed `tmp/**` output works only with explicit `--output`
- protected output paths are rejected
- absolute handoff and output paths are rejected
- malformed handoff payloads fail closed
- missing handoff authority denials fail closed
- all consumed authority denials are preserved
- no owner repo is touched
- no protected surface is touched
- no marker movement is claimed until implementation-backed proof lands

## Prompt Pack For Future Codex Worker

```text
CODEX-MSG-ID: CODEX-2026-07-06-CORTEX-READINESS-AUTHORITY-SAFE-HANDOFF-CONSUMPTION-WORKER-CLUSTER

Objective:
Implement the Cortex-side authority-safe handoff consumption proof helper admitted by:
- docs/ops/CORTEX-READINESS-AUTHORITY-SAFE-HANDOFF-CONSUMPTION-PROOF-FIRST-IMPLEMENTATION-ADMISSION-2026-07-06.md
- docs/ops/CORTEX-READINESS-AUTHORITY-SAFE-HANDOFF-CONSUMPTION-PROOF-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-06.md

Allowed files:
- ops/cortex/authority_safe_handoff_consumption.py
- tests/test_cortex_authority_safe_handoff_consumption.py
- exact implementation-backed reconciliation receipt after tests pass
- exact ATLAS Book and manifest mirrors only if implementation-backed truth changes

Hard boundaries:
- do not mutate repos/**
- do not touch Fitness, Mazer, Playbook owner repo, or any owner repo
- do not touch Supabase, Vercel, deploy, secrets, .env*, .vercel, .playwright-mcp, archive, or final receipt surfaces
- do not grant Cortex execution, approval, owner-truth, deploy, secret, transcript-scraping, automatic _stack dispatch, repo mutation, platform mutation, protected-surface mutation, or final-receipt authority

Implementation:
- build a read-only report helper with --json, --handoff, --output, and --strict
- reject absolute, parent-traversal, protected, owner-repo, final-receipt, secret, and deploy paths
- default to stdout/no writes
- write only when --output is explicit and allowed
- use deterministic JSON ordering
- validate the consumed handoff schema
- preserve every consumed authority denial
- set safe_to_use=false when the handoff is unsafe, malformed, missing required denials, or validation has critical/error counts

Verification:
- run the test and validation commands listed in the prompt-pack receipt
- commit only if validation has critical=0 error=0 and only admitted files are staged
```

## Marker Decision

No marker moves.

- `Cortex Readiness` remains `41%`.
- `Playbook Everywhere + Cortex Interface` remains `40%`.
- `AI Work Session Stability & Auto-Sync Loop` remains `85%`.
- `Sandbox Simulation Readiness` remains `99%`.
- `AI Repetition-to-Automation Pipeline` remains `38%`.
- `AI Long-Run Batch Orchestration` remains `66%`.
- `Inventory & Truth Map` remains `99%`.

## Exact Next Packet

`Cortex Readiness authority-safe handoff consumption proof implementation-readiness closeout and worker routing`

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

