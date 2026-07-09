# AI Long-Run Batch Orchestration Cross-Marker Ratchet Opportunity First-Implementation Admission

Date: 2026-07-08
Status: first_implementation_admitted
Scope: ATLAS root docs and governance only

## Objective

Admit the smallest safe future implementation slice for the cross-marker ratchet opportunity helper.

This packet does not implement the helper. It admits one bounded helper file and one bounded test file for a later prompt-pack/readiness/worker sequence.

## Why This Is The Smallest Honest Slice

The contract freeze proved the advisory boundary for cross-marker proof reuse, but it did not yet authorize a worker. The next useful step is first-implementation admission: naming the exact future files, required output fields, proof matrix, and forbidden authority so a later prompt-pack can route a worker without widening into owner repos, workflow dispatch, secrets, deploys, protected surfaces, final-receipt claims, or marker movement.

## Why This Is AI Long-Run Work

This remains `AI Long-Run Batch Orchestration` work because the target helper is an orchestration read-model over marker manifests, receipt families, proof reuse, blocked-lane state, owner-lane separation, and adjacent marker evidence. It does not improve a single owner application. It improves the long-run machinery that decides when one proof-backed execution should be surfaced as a safe advisory opportunity for another marker.

## Admitted Future Files

Future implementation file:

- `ops/atlas/cross_marker_ratchet_opportunity.py`

Future test file:

- `tests/test_atlas_cross_marker_ratchet_opportunity.py`

These names follow the existing ATLAS helper convention: root-owned orchestration helpers live under `ops/atlas/`, and direct unit coverage lives under `tests/test_atlas_*.py`.

## Admitted Helper Inputs

The future helper may read only committed root-owned or generated read-only surfaces:

- `docs/memory/initiatives/continuity-manifest-*.json`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/ops/*.md`
- JSON output from root-owned read-model helpers when invoked explicitly by the worker

The helper may treat owner-lane receipts as advisory evidence only when those receipts are already committed under ATLAS root documentation. It must not read or mutate owner repo working trees.

## Required Output Fields

The future helper must emit deterministic JSON with:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_commit`
- `source_receipts`
- `candidate_count`
- `opportunity_count`
- `opportunities`
- `blocked_candidates`
- `authority_denials`
- `owner_lane_exclusions`
- `protected_surface_exclusions`
- `marker_write_authority`
- `final_receipt_authority`

Required authority booleans:

- `marker_write_authority`: `false`
- `final_receipt_authority`: `false`

Allowed status classes:

- `ok`
- `no_opportunities`
- `blocked`
- `internal_error`

## Required Proof Matrix

Future proof must cover:

- deterministic output ordering
- a positive opportunity where one committed Cortex implementation proof also satisfies Playbook/Cortex second-consumer proof criteria
- rejection of docs-only selector receipts as ratchet proof
- rejection of docs-only contract freeze receipts as ratchet proof
- rejection of docs-only first-admission receipts as ratchet proof
- rejection of owner-lane evidence that is not committed into root governance receipts
- rejection of protected paths including `.github/workflows/**`, `.vercel/**`, `.playwright-mcp/**`, `archive/**`, `secrets/**`, and `.env*`
- rejection of uncommitted working-tree diffs as proof
- fail-closed behavior for missing receipt references
- fail-closed behavior for missing marker manifest references
- blocked classification for conflicting marker values
- blocked classification for proof that would require owner-repo mutation
- advisory-only output with no marker-write authority
- advisory-only output with no final-receipt authority
- optional JSON output limited to explicit `tmp/**.json` paths

## Forbidden Authority

The future helper must not:

- Mutate files unless writing explicitly requested JSON under `tmp/**`.
- Stage, commit, or push.
- Mutate owner repos.
- Touch Fitness or Mazer working trees.
- Touch secrets, `.env*`, `.vercel/**`, `.playwright-mcp/**`, or `archive/**`.
- Deploy or mutate platform state.
- Dispatch workflows.
- Approve or merge PRs.
- Emit final receipts.
- Move markers.
- Infer proof from green CI alone.
- Scrape hidden transcript/session state.
- Override the marker selector, continuity manifest, or operator-selected packet authority.

## Marker Decision

No marker moves from this first-implementation admission.

- `AI Long-Run Batch Orchestration` remains `69%`.
- `Cortex Readiness` remains `46%`.
- `Playbook Everywhere + Cortex Interface` remains `45%`.

## Exact Next Packet

```text
AI Long-Run Batch Orchestration cross-marker ratchet opportunity prompt-pack and worker handoff contract
```

That packet should freeze the worker objective, exact command, allowed files, forbidden files, stop conditions, output schema, and proof obligations before any implementation work starts.

## Verification

Admission basis:

- contract receipt: `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-CROSS-MARKER-RATCHET-OPPORTUNITY-CONTRACT-FREEZE-2026-07-08.md`
- prior queue fix: `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-HOUR-BLOCK-QUEUE-HELD-LANE-PROMPT-SUPPRESSION-INTEGRATION-RECONCILIATION-2026-07-08.md`
- branch: `main`
- parity before admission: `origin/main...HEAD = 0 0`
- validation before admission: `critical=0 error=0 warning=0 info=0`
- hour-block queue selected the first-implementation admission as a docs-only packet

Guardrails preserved:

- no worker implementation
- no owner-repo mutation
- no Fitness or Mazer mutation
- no protected-surface touch
- no secrets, deploys, or workflow dispatch
- no marker movement
