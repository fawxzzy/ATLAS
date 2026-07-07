# AI Repetition-to-Automation Pipeline Receipt-Derived Automation Candidate Extractor Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-07-AI-REPETITION-RECEIPT-AUTOMATION-CANDIDATE-EXTRACTOR-PROMPT-PACK`
- Date: `2026-07-07`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `prepare the future receipt-derived automation candidate extractor worker without implementing it`
- Admission basis: `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-RECEIPT-DERIVED-AUTOMATION-CANDIDATE-EXTRACTOR-FIRST-IMPLEMENTATION-ADMISSION-2026-07-07.md`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Freeze the worker handoff contract for the admitted root-owned extractor:

- future implementation file: `ops/atlas/receipt_automation_candidate_extractor.py`
- future test file: `tests/test_atlas_receipt_automation_candidate_extractor.py`

This packet does not implement either file.

## Worker Objective

Implement a read-only ATLAS-root helper that scans committed root receipts and emits deterministic JSON listing repeated automation-candidate families, rejected one-off patterns, warnings, blockers, and `safe_to_use`.

## Future CLI Contract

Expected command forms:

- `python ops/atlas/receipt_automation_candidate_extractor.py`
- `python ops/atlas/receipt_automation_candidate_extractor.py --json`
- `python ops/atlas/receipt_automation_candidate_extractor.py --source-ref <root-relative-path>`
- `python ops/atlas/receipt_automation_candidate_extractor.py --output <root-relative-path>`
- `python ops/atlas/receipt_automation_candidate_extractor.py --strict`

Expected JSON fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `candidate_count`
- `candidates`
- `rejected_candidates`
- `warnings`
- `blockers`
- `safe_to_use`

Expected status classes:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## Implementation Plan For Future Worker

1. Add `ops/atlas/receipt_automation_candidate_extractor.py`.
2. Add `tests/test_atlas_receipt_automation_candidate_extractor.py`.
3. Parse `--json`, repeated `--source-ref`, `--output`, and `--strict`.
4. Default to scanning committed `docs/ops/*.md` receipts.
5. Validate every explicit source path before reading.
6. Reject absolute paths, parent traversal, owner-repo paths, hidden transcript/session paths, secret paths, deploy/platform paths, protected paths, and unadmitted runtime paths.
7. Classify repeated receipt families deterministically.
8. Emit only the contract-frozen output fields.
9. Default to stdout/no writes.
10. Permit writes only when `--output` is explicit and allowed under `tmp/**`.
11. Return nonzero in `--strict` when the result is not safe.

## Allowed Future Files

- `ops/atlas/receipt_automation_candidate_extractor.py`
- `tests/test_atlas_receipt_automation_candidate_extractor.py`
- one implementation-backed reconciliation receipt under `docs/ops/**` after proof passes
- exact ATLAS Book and manifest mirrors only if implementation-backed truth changes

## Forbidden Future Surfaces

- `repos/**`
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- hidden transcript, chat, or session state
- deployment outputs
- platform state
- owner-repo receipts requiring owner-truth interpretation
- runtime latest files by default
- ATLAS Book, receipt index, selector, or manifest mutation by default

## Required Future Proof

Future verification must include:

- `python -m unittest tests.test_atlas_receipt_automation_candidate_extractor -v`
- `python -m unittest tests.test_atlas_marker_knockout_selector tests.test_atlas_initiative_continuity_manifest_health -v`
- `python -m unittest tests.test_atlas_ai_work_session_preflight tests.test_atlas_ai_work_session_closeout tests.test_atlas_projection_freshness tests.test_atlas_playbook_adoption_matrix -v`
- `python ops/validation/validate_stack.py`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python ops/atlas/ai_work_session_closeout.py --json --scope root`

Required proof outcomes:

- validation has `critical=0 error=0`
- default helper run writes no files
- repeated committed receipt families produce at least one candidate
- one-off committed receipt families are rejected rather than admitted
- protected source and output paths are rejected
- owner-repo, hidden transcript/session, secret, deploy, platform, archive, `.vercel`, and `.playwright-mcp` paths are rejected
- no owner repo is touched
- no protected surface is touched
- no marker movement is claimed until implementation-backed proof is reconciled

## Prompt Pack For Future Codex Worker

```text
CODEX-MSG-ID: CODEX-2026-07-07-AI-REPETITION-RECEIPT-AUTOMATION-CANDIDATE-EXTRACTOR-WORKER-CLUSTER

Objective:
Implement the read-only receipt-derived automation candidate extractor admitted by:
- docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-RECEIPT-DERIVED-AUTOMATION-CANDIDATE-EXTRACTOR-FIRST-IMPLEMENTATION-ADMISSION-2026-07-07.md
- docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-RECEIPT-DERIVED-AUTOMATION-CANDIDATE-EXTRACTOR-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-07.md

Allowed files:
- ops/atlas/receipt_automation_candidate_extractor.py
- tests/test_atlas_receipt_automation_candidate_extractor.py
- exact implementation-backed reconciliation receipt after tests pass
- exact ATLAS Book and manifest mirrors only if implementation-backed truth changes

Hard boundaries:
- do not mutate repos/**
- do not touch Fitness, Mazer, Playbook owner repo, or any owner repo
- do not touch Supabase, Vercel, deploy, secrets, .env*, .vercel, .playwright-mcp, archive, hidden transcript/session, or platform state
- do not grant execution, approval, owner-truth, deploy, secret, transcript-scraping, automatic _stack dispatch, repo mutation, platform mutation, protected-surface mutation, final-receipt, or marker-ratchet authority

Implementation:
- build a read-only report helper with --json, repeated --source-ref, --output, and --strict
- default to scanning committed docs/ops/*.md receipts
- reject absolute, parent-traversal, protected, owner-repo, hidden transcript/session, final-receipt, secret, deploy, platform, and unadmitted runtime paths
- default to stdout/no writes
- write only when --output is explicit and allowed under tmp/**
- use deterministic JSON ordering
- admit only repeated receipt-backed families with repeat_count >= 2
- reject one-off receipt patterns as rejected_candidates
- emit only the contract-frozen top-level fields

Verification:
- run the test and validation commands listed in the prompt-pack receipt
- commit only if validation has critical=0 error=0 and only admitted files are staged
```

## Marker Decision

No marker moves.

- `AI Repetition-to-Automation Pipeline` remains `38%`.
- `AI Work Session Stability & Auto-Sync Loop` remains `85%`.
- `Playbook Everywhere + Cortex Interface` remains `40%`.
- `Cortex Readiness` remains `45%`.
- `Sandbox Simulation Readiness` remains `99%`.
- `AI Long-Run Batch Orchestration` remains `66%`.
- `Inventory & Truth Map` remains `99%`.

## Exact Next Packet

`AI Repetition-to-Automation Pipeline receipt-derived automation candidate extractor implementation-readiness closeout and worker routing`

