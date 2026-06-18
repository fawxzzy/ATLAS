# Vercel Hobby Cost Governance Keep-Hobby Vs Upgrade Decision Checkpoint - 2026-06-18

- Date: `2026-06-18`
- Lane: `Vercel Hobby Cost Governance`
- Owner: `ATLAS/root`
- Mode: `root governance-checkpoint implementation plus live proof`
- Governing app: `Fawxzzy Fitness`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/ATLAS-QA-PROMOTION-RUNBOOK.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/VERCEL-HOBBY-COST-GOVERNANCE-PRESERVED-TWO-SNAPSHOT-TREND-CHECKPOINT-2026-06-18.md`
  - `ops/atlas/vercel_hobby_decision_checkpoint.py`
  - `ops/atlas/qa/release_policy.v1.json`
  - `ops/atlas/qa/release_readiness.py`
  - `tests/test_atlas_vercel_hobby_decision_checkpoint.py`
  - `tests/test_atlas_qa_pipeline.py`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.2026-06-17.json`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.2026-06-18.json`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.json`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.md`
  - `runtime/atlas/qa/release-readiness.latest.json`
  - `runtime/atlas/qa/release-readiness.latest.md`
- Control-plane checkpoint: `main@86e94271`

## Objective

Advance the lane from one preserved two-snapshot trend checkpoint to one governed keep-Hobby versus upgrade-review checkpoint that consumes preserved guardrail truth and surfaces an explicit decision inside Fitness release-readiness.

## Implementation

`ops/atlas/vercel_hobby_decision_checkpoint.py` now builds one bounded no-secret decision artifact:

- contract version `atlas.vercel_hobby_decision.v1`
- decision values:
  - `keep_hobby`
  - `upgrade_review_required`
- checkpoint status:
  - `ready`
  - `blocked`
- preserved-snapshot requirements:
  - at least two dated guardrail JSON snapshots for the same repo
  - newest preserved snapshot must align with the rolling `latest` guardrail signature
- compared signature surfaces:
  - project identity
  - deployment-enabled posture
  - route and fetch counts
  - guardrail posture
  - middleware public-path posture
  - explicit Node route list
  - watch-target inventory

`ops/atlas/qa/release_policy.v1.json` now requires a second Fitness governance check:

- `fitness_vercel_hobby_decision`

`ops/atlas/qa/release_readiness.py` now:

- records optional governance `checkpoint_status`
- records optional governance `decision`
- records optional governance `decision_reason`
- fails the governance check when a decision checkpoint is present but not `ready`
- renders the decision and reason into the markdown release-readiness report

## Live Root Proof

Decision checkpoint commands:

- `python .\ops\atlas\vercel_hobby_decision_checkpoint.py --repo-id fitness --format json --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.json`
- `python .\ops\atlas\vercel_hobby_decision_checkpoint.py --repo-id fitness --format markdown --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.md`

Observed live decision:

- `checkpoint_status: ready`
- `decision: keep_hobby`
- preserved snapshot refs:
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.2026-06-17.json`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.2026-06-18.json`
- rolling guardrail ref:
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json`
- preserved snapshot drift: `none`
- latest-alignment drift: `none`

Current decision reason:

- preserved snapshots stayed stable across the compared window
- the rolling latest guardrail still aligns with the newest preserved checkpoint
- deployment posture remains `ok`

Release-readiness command:

- `python .\ops\atlas\qa\release_readiness.py`

Observed live Fitness governance result:

- `fitness_vercel_hobby_guardrail: ready`
- `fitness_vercel_hobby_decision: ready`
- release-mode governance gate: `ready`

Important boundary:

- overall Fitness release readiness remains `blocked`
- the remaining blockers are still stale and wrong-SHA receipt provenance
- this packet closes the cost-governance lane, not the broader Fitness release gate

## Test Proof

Automated proof:

- `python -m unittest tests.test_atlas_vercel_hobby_decision_checkpoint -v`
- `python -m unittest tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_consumes_fitness_vercel_guardrail_report tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_blocks_fitness_when_guardrail_report_missing tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_consumes_fitness_vercel_hobby_decision_checkpoint tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_blocks_when_hobby_decision_checkpoint_requires_review -v`

Coverage:

- stable preserved snapshots yield `keep_hobby`
- preserved drift forces `upgrade_review_required`
- fewer than two preserved snapshots fail closed
- release-readiness consumes the decision checkpoint when it is `ready`
- release-readiness blocks when the checkpoint requires review

## Marker Movement

- `Vercel Hobby Cost Governance` moves from `85%` to `100%`

Why `100%` is honest:

- the lane now has the exact broader governed operating checkpoint it previously lacked
- preserved trend truth now drives one explicit keep-Hobby versus upgrade-review decision rather than only providing passive evidence
- the decision is machine-readable, rerunnable, policy-bound, release-readiness-visible, and test-backed

Why this does not overclaim:

- the checkpoint is still repo-local and no-secret
- it does not claim live Vercel billing counter truth
- it does not claim Fitness is currently release-ready
- it does not mutate Vercel settings, billing, or project linkage

## Exact Next Honest Move

- none for this lane; future work would be a reopen only if the preserved guardrail window drifts enough to force `upgrade_review_required` or if the governing checkpoint contract regresses

## Validation

- `python -m unittest tests.test_atlas_vercel_hobby_decision_checkpoint -v`
- `python -m unittest tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_consumes_fitness_vercel_guardrail_report tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_blocks_fitness_when_guardrail_report_missing tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_consumes_fitness_vercel_hobby_decision_checkpoint tests.test_atlas_qa_pipeline.AtlasQaPipelineTests.test_release_readiness_blocks_when_hobby_decision_checkpoint_requires_review -v`
- `python .\ops\atlas\vercel_hobby_decision_checkpoint.py --repo-id fitness --format json --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.json`
- `python .\ops\atlas\vercel_hobby_decision_checkpoint.py --repo-id fitness --format markdown --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.md`
- `python .\ops\atlas\qa\release_readiness.py`

Result:

- focused decision-checkpoint tests passed
- focused release-readiness governance tests passed
- live decision artifact emitted successfully
- live release-readiness now surfaces the explicit Fitness Hobby decision checkpoint
