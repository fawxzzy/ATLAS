# Cortex Readiness Second Advisory Substrate Consumption First-Implementation Admission - 2026-07-08

- CODEX-MSG-ID: `CODEX-2026-07-08-CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-FIRST-IMPLEMENTATION-ADMISSION`
- Date: `2026-07-08`
- Mode: `docs-only first-implementation admission`
- Scope: `admit the smallest future Cortex-side implementation slice for the second advisory substrate consumer`
- Contract basis: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-CONTRACT-FREEZE-2026-07-08.md`
- Branch basis: `main@420463ed457af3553e6246282f0ed17ec5ab4795`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Admit one future implementation slice:

`second_advisory_substrate_consumption`

This slice may become a read-only Cortex-side helper that consumes one explicit, root-owned advisory substrate source class beyond the already implemented authority-safe handoff consumer.

This packet does not implement the helper or tests.

## 1. Admitted Implementation Slice

The admitted future slice is a deterministic report helper that consumes one explicit root-relative source ref, classifies it as an admitted second advisory substrate, validates the source shape, preserves all authority denials, and emits only advisory consumption output.

The first default admitted source class is the Cortex continuity/restart substrate:

- `docs/memory/initiatives/continuity-manifest-cortex-readiness.json`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

The helper may also accept the other admitted root-owned source classes frozen by the contract basis after implementation proves their guards.

## 2. Why This Is Cortex Readiness

The Playbook/Cortex lane already produced the first authority-safe interface handoff helper. Cortex Readiness then proved a first Cortex-side consumer through `ops/cortex/authority_safe_handoff_consumption.py`.

This packet is Cortex Readiness work because it admits a second Cortex-side advisory consumer family. It is not Playbook/Cortex same-lane work because it does not widen the Playbook interface or Foundation owner-lane proof. It only prepares Cortex to consume a second root-owned advisory substrate without becoming an authority surface.

## 3. No Execution Authority

The admitted helper must never execute, approve, dispatch, deploy, mutate, or issue final receipts. It may only classify explicit root-owned substrate and report advisory findings.

It must not:

- dispatch `_stack`
- approve work
- create final receipts
- mutate ATLAS Book mirrors
- mutate manifests
- mutate runtime latest files by default
- mutate owner repos
- mutate Fitness or Mazer
- call deploy, platform, or secret surfaces
- claim owner-truth authority
- claim marker authority

## 4. Second Advisory Substrate Source Class

The admitted second source class is explicit root-owned Cortex/read-model substrate, distinct from the first implemented authority-safe handoff payload class.

The first source class already exists:

- producer: `ops/cortex/authority_safe_interface_handoff.py`
- consumer: `ops/cortex/authority_safe_handoff_consumption.py`
- proof: `tests/test_cortex_authority_safe_handoff_consumption.py`

The admitted second class is not a handoff payload. It is a root-owned advisory substrate reference that Cortex can classify and summarize without treating it as execution authority or owner truth.

## 5. Source Surfaces Already Proven

The first substrate path already proves:

- explicit source artifact consumption
- root-relative path guards
- protected-path rejection
- authority-denial preservation
- deterministic JSON output
- default no-write behavior
- safe `tmp/**` output gating
- validation critical/error gating before `safe_to_use=true`

The second consumer must preserve those standards while consuming a different source class.

## 6. Allowed Source Surfaces

The future helper may consume only explicit ATLAS-root sources from the contract-freeze admitted classes:

- Cortex manifests and restart mirrors
- Cortex and Playbook/Cortex authority receipts
- existing Cortex advisory runtime artifacts
- validation and continuity proof outputs
- existing Cortex helpers and tests as read-only contract references

Every source must be root-relative and must remain inside the ATLAS root.

## 7. Excluded Source Surfaces

The future helper must reject:

- `repos/**`
- Fitness owner-lane sources
- Mazer owner-lane sources
- owner-repo receipts as truth inputs
- hidden transcript, chat, or session state
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- deploy or platform output
- any source outside the ATLAS root
- any absolute path source
- any parent-traversal source

## 8. Admitted Output Surface

The future helper may emit:

- stdout human summary
- deterministic JSON through `--json`
- one explicit root-relative `--output <path>` artifact only when the path is allowed

Allowed output must be root-relative and under `tmp/**`.

Default mode must write no files.

## 9. Advisory-Only Result

The helper may emit advisory findings such as:

- source classification
- source digest
- substrate class
- whether the source is admitted
- whether required source fields or references are present
- preserved authority denials
- warnings, blockers, and `safe_to_use`

It must not emit final receipts, approval decisions, deployment decisions, owner-truth claims, marker decisions, or mutation instructions.

## 10. Forbidden Authority

The future helper must preserve denials for:

- execution
- approval
- owner-truth
- final-receipt
- deploy
- secret-handling
- transcript-scraping
- automatic `_stack` dispatch
- repo mutation
- platform mutation
- owner-repo mutation
- protected-surface mutation
- marker movement

## 11. Future Implementation File

Admitted future file:

`ops/cortex/second_advisory_substrate_consumption.py`

This follows the local Cortex helper convention and makes the second-consumer role explicit. It is intentionally distinct from `authority_safe_handoff_consumption.py`.

## 12. Future Test File

Admitted future test file:

`tests/test_cortex_second_advisory_substrate_consumption.py`

## 13. Future Proof Matrix

The future implementation must prove:

1. valid second advisory substrate consumed safely
2. malformed source blocked
3. owner-repo source rejected unless explicitly admitted read-only by a future contract
4. hidden transcript source rejected
5. deploy/platform/secret path rejected
6. output path guard rejects absolute paths
7. output path guard rejects protected paths
8. safe `tmp/**.json` output accepted
9. deterministic JSON ordering
10. preserved authority denials prove no execution, final-receipt, owner-truth, deploy, secret, workflow-dispatch, owner-repo mutation, protected-surface mutation, or marker authority

## 14. Non-Goals

This packet does not:

- implement `ops/cortex/second_advisory_substrate_consumption.py`
- add `tests/test_cortex_second_advisory_substrate_consumption.py`
- mutate Fitness
- mutate Mazer
- mutate Playbook owner repo
- mutate any owner repo
- mutate Supabase or Vercel
- deploy or publish
- read or write secrets
- touch `.env*`, `.vercel/`, `.playwright-mcp/`, `archive/`, or `secrets/`
- move markers
- grant Cortex execution readiness

## Marker Decision

No marker moves.

- `Cortex Readiness` remains `45%`.
- `Sandbox Simulation Readiness` remains `99%`.
- `AI Repetition-to-Automation Pipeline` remains `54%`.
- `AI Long-Run Batch Orchestration` remains `69%`.
- `AI Work Session Stability & Auto-Sync Loop` remains `85%`.
- `Playbook Everywhere + Cortex Interface` remains `40%`.

## Exact Next Packet

`Cortex Readiness second advisory substrate consumption prompt-pack and worker handoff contract`
