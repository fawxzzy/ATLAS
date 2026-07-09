# AI Long-Run Batch Orchestration Cross-Marker Ratchet Opportunity Prompt-Pack And Worker Handoff Contract

Date: 2026-07-08
Status: prompt_pack_frozen
Scope: ATLAS root docs and governance only

## Result

The cross-marker ratchet opportunity worker handoff contract is frozen.

This remains a docs-only packet. It does not implement the worker.

## Worker Objective

Implement one bounded, read-only ATLAS-root helper that reports advisory opportunities where one committed proof-backed execution appears to satisfy more than one marker's ratchet criteria.

The worker must create:

- `ops/atlas/cross_marker_ratchet_opportunity.py`
- `tests/test_atlas_cross_marker_ratchet_opportunity.py`

Primary command:

```powershell
python ops\atlas\cross_marker_ratchet_opportunity.py --json
```

Optional safe output command:

```powershell
python ops\atlas\cross_marker_ratchet_opportunity.py --json --output tmp/atlas/cross-marker-ratchet-opportunity.latest.json
```

## Required Behavior

The helper must:

- Emit deterministic JSON.
- Read only committed ATLAS-root governed inputs.
- Identify candidate receipts that may support more than one marker's ratchet criteria.
- Distinguish implementation-backed proof from selector-only, contract-only, admission-only, and wording-only receipts.
- Preserve Fitness and Mazer as separate owner lanes.
- Preserve Cortex and Playbook refs as advisory evidence only.
- Reject owner-repo working-tree reads and mutations.
- Reject protected, secret, deploy, workflow, hidden transcript, absolute-path, and parent-traversal inputs.
- Fail closed on missing or malformed required inputs.
- Write only to explicit `tmp/**.json` output paths when `--output` is supplied.

## Required Output Schema

The helper must emit:

```json
{
  "schema_version": "atlas.cross_marker_ratchet_opportunity.v1",
  "status": "ok",
  "safe_to_use": true,
  "basis_commit": null,
  "source_receipts": [],
  "candidate_count": 0,
  "opportunity_count": 0,
  "opportunities": [],
  "blocked_candidates": [],
  "authority_denials": [],
  "owner_lane_exclusions": [],
  "protected_surface_exclusions": [],
  "marker_write_authority": false,
  "final_receipt_authority": false
}
```

Allowed `status` values:

- `ok`
- `no_opportunities`
- `blocked`
- `internal_error`

Required authority values:

- `marker_write_authority`: `false`
- `final_receipt_authority`: `false`

## Opportunity Record Shape

Each opportunity record must include:

- `source_receipt`
- `source_marker`
- `candidate_marker`
- `candidate_marker_percent`
- `evidence_class`
- `ratchet_condition_refs`
- `reuse_basis`
- `limits`
- `required_follow_up_packet`
- `safe_to_use`

The helper may recommend a follow-up packet, but that recommendation is advisory. It cannot move a marker or emit a final receipt.

## Blocked Candidate Shape

Each blocked candidate must include:

- `source_receipt`
- `candidate_marker`
- `blocker_class`
- `reason`
- `required_unblock`

Frozen blocker classes:

- `docs_only_receipt`
- `owner_lane_evidence_only`
- `protected_surface_required`
- `uncommitted_evidence`
- `missing_receipt`
- `missing_manifest`
- `conflicting_marker_truth`
- `requires_owner_mutation`
- `requires_deploy_or_secret`
- `requires_workflow_authority`

## Admitted Inputs

The worker may read:

- `docs/memory/initiatives/continuity-manifest-*.json`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- committed `docs/ops/*.md` receipts
- JSON output from root-owned read-model helpers when invoked explicitly by the worker

The worker may call, read-only:

- `python ops\atlas\marker_aware_next_packet_planner.py --json`
- `python ops\atlas\continuity_manifest_health.py`
- `python ops\atlas\continuity_open_marker_restart_index.py`
- `python ops\atlas\continuity_coverage.py`

## Proof Obligations

The test suite must cover:

- deterministic output ordering
- live root input path returns `ok` or `no_opportunities`
- positive opportunity detection for the Cortex second advisory substrate proof also satisfying Playbook/Cortex second-consumer criteria
- rejection of selector-only receipts as ratchet proof
- rejection of contract-freeze receipts as ratchet proof
- rejection of first-implementation admission receipts as ratchet proof
- rejection of prompt-pack receipts as ratchet proof
- rejection of owner-lane evidence that is not committed into ATLAS root governance receipts
- rejection of protected paths
- rejection of uncommitted working-tree diffs as proof
- fail-closed behavior for missing receipt refs
- fail-closed behavior for missing manifest refs
- blocked classification for conflicting marker values
- blocked classification for proof that would require owner-repo mutation
- blocked classification for proof that would require deploy, secret, or workflow authority
- explicit safe `tmp/**` JSON output path handling if output writing is implemented
- no marker movement or final-receipt authority appears in output

## Allowed Touch Surface For Implementation

Only these implementation surfaces are admitted by the eventual worker packet:

- `ops/atlas/cross_marker_ratchet_opportunity.py`
- `tests/test_atlas_cross_marker_ratchet_opportunity.py`

Worker reconciliation may also add one bounded reconciliation receipt and exact Book/manifest mirrors after proof passes.

## Forbidden Surfaces

The worker and implementation packet must not touch:

- `repos/**`
- Fitness owner repo files
- Mazer owner repo files
- Playbook owner repo files
- `secrets/**`
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- `.github/workflows/**`
- deploy or platform surfaces
- broad untracked backlog

## Forbidden Authority

The worker must not:

- Mutate files except an explicitly passed safe `tmp/**` JSON output path if that output option is implemented.
- Stage, commit, or push.
- Mutate owner repos.
- Touch Fitness or Mazer.
- Touch secrets.
- Deploy.
- Dispatch workflows.
- Approve or merge PRs.
- Emit final receipts.
- Move markers.
- Treat Cortex advisory output as execution authority.
- Treat Playbook refs as owner-truth authority.
- Infer proof from green CI alone.

## Stop Conditions

The worker must stop or emit `blocked` / `internal_error` without fabricating an opportunity if:

- Stack validation has `critical` or `error`.
- Required marker or manifest inputs are missing.
- Input sources include protected, owner, secret, deploy, workflow, hidden, absolute, or parent-traversal paths.
- The opportunity would require owner mutation, workflow dispatch, deploy, secret handling, platform mutation, or protected-surface access.
- Proof is missing for a proof-gated opportunity.

## Marker Decision

No marker moves from this prompt-pack.

- `AI Long-Run Batch Orchestration` remains `69%`.
- `Cortex Readiness` remains `46%`.
- `Playbook Everywhere + Cortex Interface` remains `45%`.

## Exact Next Packet

```text
AI Long-Run Batch Orchestration cross-marker ratchet opportunity implementation-readiness closeout and worker routing
```

That packet should confirm no docs-only prerequisite remains before the bounded implementation worker.
