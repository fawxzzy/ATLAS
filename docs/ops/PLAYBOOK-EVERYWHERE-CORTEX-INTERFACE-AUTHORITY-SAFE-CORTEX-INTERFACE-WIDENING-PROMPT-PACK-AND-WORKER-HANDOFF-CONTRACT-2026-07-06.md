# Playbook Everywhere + Cortex Interface Authority-Safe Cortex Interface Widening Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-06-PLAYBOOK-CORTEX-AUTHORITY-SAFE-INTERFACE-WIDENING-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT`
- Date: `2026-07-06`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `prepare the implementation handoff for the admitted authority-safe Cortex interface helper without implementing it`
- Branch basis: `main@0324d75073b57ddc94fa0a435b6cd9330d0daa51`
- Admission basis: `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-FIRST-IMPLEMENTATION-ADMISSION-2026-07-06.md`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Freeze the worker handoff contract for implementing the admitted helper:

- future implementation file: `ops/cortex/authority_safe_interface_handoff.py`
- future test file: `tests/test_cortex_authority_safe_interface_handoff.py`

This packet does not implement either file. It packages the exact prompt and proof boundaries for a later worker.

## Worker Objective

Implement a root-owned, read-only advisory Cortex interface handoff helper that converts explicit ATLAS/Playbook/Cortex source refs into a bounded handoff payload without granting Cortex execution, approval, owner-truth, deploy, secret, transcript-scraping, automatic `_stack` dispatch, repo mutation, platform mutation, or final-receipt authority.

## Implementation Plan For Future Worker

1. Add `ops/cortex/authority_safe_interface_handoff.py`.
2. Add `tests/test_cortex_authority_safe_interface_handoff.py`.
3. Implement a deterministic report builder with `schema_version`, `status`, `root`, `branch`, `head`, `source_refs`, `consumed_surfaces`, `handoff_payload`, `authority_denials`, `forbidden_surfaces`, `warnings`, `blockers`, and `safe_to_use`.
4. Accept `--json`, `--scope root|research`, repeatable `--source <path>`, `--output <root-relative-path>`, and `--strict`.
5. Default to read-only stdout behavior.
6. Permit file writes only when `--output` is explicit and the path is root-relative, inside the ATLAS root, and not under protected surfaces.
7. Reject absolute paths, parent traversal, protected roots, owner repo paths, secrets, deploy/platform surfaces, runtime writeback outside an explicitly admitted future packet, and final receipt paths.
8. Read only admitted source surfaces from the first-implementation admission receipt.
9. Derive `safe_to_use=false` when stack validation has critical or error counts.
10. Keep output advisory: a recommended packet and handoff payload only, never execution.

## Files To Modify In Future Worker

Allowed future files:

- `ops/cortex/authority_safe_interface_handoff.py`
- `tests/test_cortex_authority_safe_interface_handoff.py`
- one future reconciliation receipt under `docs/ops/**`
- exact ATLAS Book and manifest mirrors only if implementation-backed truth changes

Forbidden future files and surfaces:

- `repos/**`
- `runtime/**` except explicitly admitted output in a later packet
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- deployment outputs
- owner-repo receipts
- final Lifeline receipts

## Required Source Refs For Future Worker

The worker may consume only explicit root-owned refs:

- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`
- `docs/standards/WORKER-ORCHESTRATION.md`
- `docs/PLAYBOOK_NOTES.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/memory/initiatives/continuity-manifest-playbook-everywhere-cortex-interface.json`
- `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-*.md`
- `ops/atlas/playbook_adoption_matrix.py`
- `ops/cortex/worker_prompt.py`
- `runtime/cortex/worker-prompts/latest.json`
- `runtime/receipts/validation/stack-validation.latest.json`
- `stack.lock.yaml`

The worker must fail closed if a requested source is outside the admitted set or under `repos/**`.

## Verification Steps For Future Worker

Future worker verification must include:

- `python -m unittest tests.test_cortex_authority_safe_interface_handoff -v`
- `python -m unittest tests.test_cortex_worker_prompt tests.test_cortex_worker_plan tests.test_cortex_stack_consumption_pilot tests.test_cortex_stack_handoff -v`
- `python -m unittest tests.test_atlas_ai_work_session_preflight tests.test_atlas_ai_work_session_closeout tests.test_atlas_projection_freshness tests.test_atlas_playbook_adoption_matrix -v`
- `python ops/validation/validate_stack.py`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python ops/atlas/ai_work_session_closeout.py --json --scope root`

Expected proof outcomes:

- validation has `critical=0 error=0`
- owner repos are not touched
- protected surfaces are not touched
- default helper run writes no files
- explicit allowed `tmp/**` output works
- protected output paths are rejected
- absolute output paths are rejected
- final receipt output is rejected
- deterministic JSON ordering is proven

## Prompt Pack For Future Codex Worker

```text
CODEX-MSG-ID: CODEX-2026-07-06-PLAYBOOK-CORTEX-AUTHORITY-SAFE-INTERFACE-WIDENING-WORKER-CLUSTER

Objective:
Implement the authority-safe Cortex interface handoff helper admitted by:
- docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-FIRST-IMPLEMENTATION-ADMISSION-2026-07-06.md
- docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-06.md

Allowed files:
- ops/cortex/authority_safe_interface_handoff.py
- tests/test_cortex_authority_safe_interface_handoff.py
- exact docs/ops reconciliation receipt after tests pass
- exact ATLAS Book and manifest mirrors only if implementation-backed truth changes

Hard boundaries:
- do not mutate repos/**
- do not touch Fitness, Mazer, Playbook owner repo, or any owner repo
- do not touch Supabase, Vercel, deploy, secrets, .env*, .vercel, .playwright-mcp, archive, or final receipt surfaces
- do not grant Cortex execution, approval, owner-truth, deploy, secret, transcript-scraping, automatic _stack dispatch, repo mutation, platform mutation, or final-receipt authority

Implementation:
- build a read-only report helper with --json, --scope root|research, repeatable --source, --output, and --strict
- reject absolute, parent-traversal, protected, owner-repo, final-receipt, secret, and deploy output paths
- default to stdout/no writes
- write only when --output is explicit and allowed
- use deterministic JSON ordering
- set safe_to_use=false when validation has critical or error counts

Verification:
- run the test and validation commands listed in the prompt-pack receipt
- commit only if validation has critical=0 error=0 and only admitted files are staged
```

## Marker Decision

No marker moves from this prompt-pack.

- `Playbook Everywhere + Cortex Interface`: remains `30%`
- `Cortex Readiness`: remains `41%`
- `AI Work Session Stability & Auto-Sync Loop`: remains `85%`

Reason: this packet prepares implementation, but no helper or tests have landed yet.

## Exact Next Packet

Next exact packet:

`Playbook Everywhere + Cortex Interface authority-safe Cortex interface widening implementation-readiness closeout and worker routing`

That packet should decide whether the implementation worker can run from this prompt pack. It should not claim marker movement unless the helper and tests have actually landed in a later worker-cluster reconciliation.

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
