# AI Repetition-to-Automation Pipeline Receipt-Derived Automation Candidate Review Surface Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-07-AI-REPETITION-RECEIPT-AUTOMATION-CANDIDATE-REVIEW-SURFACE-PROMPT-PACK`
- Date: `2026-07-07`
- Mode: `prompt-pack and worker handoff contract`
- Scope: `freeze the worker objective and proof matrix for candidate-review implementation`
- Admission basis: `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-RECEIPT-DERIVED-AUTOMATION-CANDIDATE-REVIEW-SURFACE-FIRST-IMPLEMENTATION-ADMISSION-2026-07-07.md`
- Branch basis: `main@f77c0067`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Worker Objective

Implement `ops/atlas/receipt_automation_candidate_review.py` and `tests/test_atlas_receipt_automation_candidate_review.py`.

The helper must consume live extractor output or an explicit `tmp/**` extractor report and emit advisory review cards only.

## Required CLI

- `python ops/atlas/receipt_automation_candidate_review.py`
- `--json`
- `--candidate-report tmp/<file>.json`
- `--output tmp/<file>.json`
- `--strict`

## Preserved Boundaries

The worker must preserve:

- read-only default behavior
- `tmp/**` only for input report and output writes
- no owner-repo reads or writes
- no hidden transcript/session/chat reads
- no secrets
- no deploy or platform calls
- no `_stack` dispatch
- no marker fields
- no marker movement

## Exact Next Packet

`AI Repetition-to-Automation Pipeline receipt-derived automation candidate review surface implementation-readiness closeout and worker routing`

## Marker Decision

No marker moves from prompt-pack routing alone.

`AI Repetition-to-Automation Pipeline` remains `39%`.
