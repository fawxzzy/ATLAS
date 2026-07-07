# AI Repetition-to-Automation Pipeline Receipt-Derived Automation Candidate Review Surface Contract Freeze

- CODEX-MSG-ID: `CODEX-2026-07-07-AI-REPETITION-RECEIPT-AUTOMATION-CANDIDATE-REVIEW-SURFACE-CONTRACT-FREEZE`
- Date: `2026-07-07`
- Mode: `contract freeze`
- Scope: `define how extractor candidates can become bounded advisory review cards`
- Basis: `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-RECEIPT-DERIVED-AUTOMATION-CANDIDATE-EXTRACTOR-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-07.md`
- Branch basis: `main@f77c0067`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Contract

The candidate-review surface may consume the read-only extractor report and emit deterministic advisory review cards.

The review surface may:

- read live extractor output from `ops/atlas/receipt_automation_candidate_extractor.py`
- optionally read a precomputed extractor JSON report only from `tmp/**`
- rank review cards by bounded category priority and repeat count
- emit the next review packet for each candidate
- preserve inherited no-owner, no-secret, no-deploy, no-hidden-context, no-`_stack`, and no-marker boundaries

The review surface must not:

- treat a candidate as approved implementation work
- infer marker movement
- infer owner-repo truth
- read hidden transcripts, sessions, chats, or `.codex/**`
- read or write secrets, `.env*`, `.vercel/**`, `.playwright-mcp/**`, `archive/**`, or `repos/**`
- dispatch `_stack`
- mutate any owner repo
- deploy, publish, or call platform APIs

## Admitted Future Files

- `ops/atlas/receipt_automation_candidate_review.py`
- `tests/test_atlas_receipt_automation_candidate_review.py`

## Required Output Contract

The future helper must emit a deterministic JSON object with these top-level fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `candidate_report_ref`
- `source_report_schema`
- `source_report_status`
- `candidate_count`
- `review_count`
- `reviews`
- `warnings`
- `blockers`
- `safe_to_use`

The helper must not emit marker or marker-movement fields.

## Exact Next Packet

`AI Repetition-to-Automation Pipeline receipt-derived automation candidate review surface first-implementation admission`

## Marker Decision

No marker moves from this contract freeze alone.

`AI Repetition-to-Automation Pipeline` remains `39%`.
