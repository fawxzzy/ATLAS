# Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory prompt-pack and worker handoff contract

- Date: `2026-07-09`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only prompt-pack contract`
- Control-plane checkpoint: `main@01216be3`
- Marker movement: none

## Worker Objective

Implement one bounded helper/test pair so `ops/cortex/chatgpt_codex_role_inventory.py` can classify current ChatGPT/Codex scaffolding duties against the frozen Cortex dual-mode operating model, emit deterministic advisory inventory JSON, and preserve all authority denials.

## Exact Files

The worker may touch only:

- `ops/cortex/chatgpt_codex_role_inventory.py`
- `tests/test_cortex_chatgpt_codex_role_inventory.py`

## Exact Input Contract

The helper must read only these root-owned doctrine surfaces:

- `docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-OPERATING-MODE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `AGENTS.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/registry/STACK-REPO-INVENTORY.json`

The helper must reject or ignore:

- hidden transcript sources
- external session/browser state
- owner-repo receipts as primary role truth
- uncommitted diffs
- absolute or parent-traversal references if any future file-ref surface is introduced

## Exact Role Classification Contract

The worker must implement deterministic current-role classification only for these admitted role classes:

- `synthesis_strategy`
- `research_synthesis`
- `packet_framing`
- `operator_facing_tradeoff_compression`
- `execution_mutation`
- `verification_and_tests`
- `proof_and_receipt_capture`
- `execution_reconciliation`

Each role record must map to one admitted future target:

- `cortex_synthesis_interface`
- `cortex_execution_interface`
- `cortex_bridge`
- `shared_atlas_substrate`
- `shared_playbook_doctrine_substrate`

No simulation-role mapping is admitted in this worker.

## Exact CLI Contract

Required flags:

- `--json` optional JSON-only stdout mode
- `--output` optional root-relative `tmp/**.json` output path
- `--strict` optional blocker-sensitive exit mode

The helper must reject:

- absolute output paths
- parent traversal in output paths
- protected output paths
- output paths outside root-relative `tmp/**.json`

## Exact Helper Contract

The worker must implement a helper that:

1. validates presence of the admitted doctrine inputs
2. derives one deterministic current-role inventory from those inputs
3. maps each current role to one future Cortex target
4. reports shared substrate dependencies explicitly
5. reports authority denials explicitly
6. reports split-brain risks explicitly
7. fails closed when the operating-model truth is missing or contradictory

The helper may not:

- infer historical role usage from hidden transcripts
- query external products
- read secrets or `.env*`
- mutate repos
- stage, commit, or push

## Exact Output Contract

The helper output must emit schema version:

```text
atlas.cortex.chatgpt_codex_role_inventory.v1
```

Allowed statuses:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

Required top-level fields:

- `schema_version`
- `status`
- `safe_to_use`
- `current_role_count`
- `mapped_role_count`
- `unmapped_role_count`
- `current_roles`
- `future_interface_targets`
- `shared_substrate_dependencies`
- `authority_denials`
- `split_brain_risks`
- `warnings`
- `blockers`

## Exact Role Record Contract

Each role record may use only:

- `role_id`
- `current_role_class`
- `current_system`
- `role_summary`
- `future_target`
- `shared_substrate_dependency`
- `authority_requirements`
- `migration_notes`

The helper may not emit:

- transcript excerpts
- external session ids
- secret-bearing product data
- owner-repo mutation plans

## Exact Shared-Substrate Contract

The helper must expose shared-substrate dependency output for:

- ATLAS receipts/manifests/Book/read-model truth
- Playbook doctrine/pattern/failure-mode truth

It may not silently collapse those into generic notes.

## Exact Risk Contract

The helper must be able to report at least:

- `memory_truth_split`
- `doctrine_truth_split`
- `execution_truth_split`
- `marker_authority_split`
- `bridge_scope_ambiguity`

These are warnings or blockers only. They must not trigger autonomous escalation.

## Exact Proof Commands

The worker must run:

1. `python -m unittest tests.test_cortex_chatgpt_codex_role_inventory -v`
2. `python ops/cortex/chatgpt_codex_role_inventory.py --json`
3. one root-safe helper proof command with `--output tmp/cortex-role-inventory-smoke.json`
4. `python ops/validation/validate_stack.py`
5. `git status --short`
6. `git diff --name-only`

## Exact Required Proof Matrix

The worker proof must cover at least:

1. deterministic classification of ChatGPT-style synthesis duties
2. deterministic classification of Codex-style execution duties
3. deterministic bridge-role mapping
4. explicit ATLAS shared-substrate dependency output
5. explicit Playbook shared-substrate dependency output
6. failure-closed behavior when the operating-model receipt is missing
7. failure-closed behavior when required role classes cannot be mapped safely
8. rejection of hidden transcript or external-session source attempts
9. safe `tmp/**.json` output acceptance
10. protected or absolute output-path rejection
11. deterministic JSON ordering
12. `--strict` returns nonzero on blockers

## Exact Forbidden Authority

The worker must not:

- touch owner repos
- read or print secrets
- read `.env*`
- touch deploy or workflow surfaces
- widen into simulation mapping
- move markers
- emit final receipts
- add files outside the admitted helper/test pair
- widen into Book or restart-guide edits

## Exact Stop Conditions

Stop and return without implementation if the worker would require:

- hidden transcript scraping
- external product/API access
- owner-repo mutation
- secret, deploy, or workflow authority
- simulation-role widening
- marker movement
- file additions beyond the admitted pair

## Next

Open only this next packet:

```text
Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory implementation-readiness closeout and worker routing
```
