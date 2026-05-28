# Local Data Gateway Repo Naming Rename-Manifest Contract Checkpoint - 2026-05-28

- Date: `2026-05-28`
- Owner: ATLAS root
- Mode: `docs-only contract checkpoint`
- Scope: `repo-naming local-only rename-manifest contract shape`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-EXPANSION-PASS-2-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-PROOF-PASS-1-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-9-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-AUTHORIZATION-PREREQUISITES-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-BOUNDED-REWRITE-ROLLBACK-PLAN-2026-05-28.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@993806a`

## Objective

Define the exact Local Data Gateway contract slice needed for repo-naming canonicalization workflows without widening into send-capable behavior, implementation changes, or rename execution.

This checkpoint does not:

- modify `_stack`
- imply `adoptable now` graduation for repo naming workflows
- authorize any `send`, `sync`, `post`, `submit`, or `mutate` behavior
- rename any repo
- rename any remote
- imply any GitHub-side rename
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `993806a`
- status: clean except intentional untracked `archive/`
- validation: green before drafting at `critical=0 error=0 warning=310`

## Adoption Map Recomputed

The currently proven `adoptable now` set remains unchanged:

- Supabase export / approval-prep packet workflows
- Vercel dependency / deletion decision workflows
- DiscordOS trust-boundary / provenance proof workflows

Repo naming execution/proof packets remain:

- `adoptable later`

Why they remain below graduation:

- the family is still local-only and bounded
- but it still depends on rename-specific candidate identity, rewrite scope, rollback order, and reconciliation semantics that the current generic packet chain does not yet encode

This checkpoint narrows that missing contract.

It does not prove the family is already admitted.

## Contract Goal

The missing reusable artifact for repo naming workflows is one local-only rename manifest that can describe:

- which rename candidate is under review
- which current-truth surfaces are expected to change
- what exact rollback order applies
- what no-send assertions remain in force
- what proof/reconciliation outputs must exist after execution or blocked execution

That artifact should make later no-send packet reuse less ambiguous without smuggling rename-specific execution logic into the gateway.

## Exact Rename-Manifest Contract Slice

The future rename-manifest packet should contain these top-level sections:

1. `candidate_identity`
2. `rewrite_surface_inventory`
3. `rollback_order`
4. `no_send_attestation`
5. `proof_reconciliation_expectations`

The contract below freezes what each section must express.

## `candidate_identity`

Required fields:

- `lane`
- `candidate_id`
- `source_local_path`
- `target_local_path`
- `candidate_class`
- `approval_receipt`
- `rewrite_plan_receipt`
- `current_marker_posture`
- `exception_boundary`

Required meanings:

- `lane`
  - must be `atlas-owned-repo-naming-canonicalization`
- `candidate_id`
  - stable identifier such as `stream-safe-first-pass`
- `source_local_path`
  - current canonical local repo path under `repos/`
- `target_local_path`
  - proposed canonical local repo path under `repos/`
- `candidate_class`
  - one of:
    - `safe-first-approved`
    - `later-candidate`
    - `blocked`
    - `preserved-exception`
- `approval_receipt`
  - exact receipt that approved the candidate if approval exists
- `rewrite_plan_receipt`
  - exact receipt that froze rewrite and rollback order
- `current_marker_posture`
  - current lane marker value at manifest creation time
- `exception_boundary`
  - explicit statement that the manifest does not reopen:
    - `fawxzzy-fitness`
    - remote rename
    - GitHub-side rename

## `rewrite_surface_inventory`

Required fields:

- `local_directory_rename`
- `registry_surfaces`
- `inventory_surfaces`
- `current_truth_surfaces`
- `receipt_index_surfaces`
- `expected_noop_checks`
- `historical_receipt_rewrite_rule`

Required meanings:

- `local_directory_rename`
  - the one exact local rename under `repos/`
- `registry_surfaces`
  - canonical registry files expected to change:
    - `stack.yaml`
    - `stack.lock.yaml`
- `inventory_surfaces`
  - canonical inventory/truth-map publications expected to change:
    - `docs/registry/STACK-REPO-INVENTORY.json`
    - `docs/audits/STACK-REPO-INVENTORY.md`
- `current_truth_surfaces`
  - active ATLAS surfaces expected to change only when they currently name the old path
- `receipt_index_surfaces`
  - at minimum:
    - `docs/atlas-book/05-receipt-index.md`
- `expected_noop_checks`
  - surfaces that must be checked but may legitimately remain unchanged
- `historical_receipt_rewrite_rule`
  - explicit rule that historical receipts are preserved unless they are current-truth surfaces by design

## `rollback_order`

Required fields:

- `rollback_required_if`
- `rollback_steps`
- `rollback_validation_command`
- `rollback_scope_limit`

Required meanings:

- `rollback_required_if`
  - exact conditions that force rollback before the packet can be considered complete
- `rollback_steps`
  - ordered reverse sequence of the approved rewrite order
- `rollback_validation_command`
  - current stack validation command
- `rollback_scope_limit`
  - explicit statement that rollback restores only:
    - local directory truth
    - ATLAS control-plane truth
  - and does not imply:
    - remote rename reversal
    - GitHub-side rename reversal

Minimum rollback step vocabulary:

1. revert current-truth book and receipt updates
2. revert inventory publications
3. revert registry files
4. rename local directory back to source path
5. rerun validation

## `no_send_attestation`

Required fields:

- `downstream_send_performed`
- `downstream_execution_performed`
- `remote_target_selected`
- `automatic_handoff_authorized`
- `remote_name_assumed`
- `github_name_assumed`
- `owner_repo_runtime_mutation_performed`

Required values for this family:

- all must remain `false`

Required narrative note:

- the rename manifest is a local control-plane packet only
- it cannot authorize transport, target selection, remote mutation, or owner-repo runtime changes

## `proof_reconciliation_expectations`

Required fields:

- `execution_outcome_class`
- `required_execution_receipt`
- `required_proof_receipt`
- `canonical_path_truth_checks`
- `stale_reference_check_scope`
- `reconciliation_allowed_scope`
- `blocked_execution_allowed`

Required meanings:

- `execution_outcome_class`
  - one of:
    - `blocked-before-rename`
    - `executed-local-rename`
- `required_execution_receipt`
  - exact later receipt path that records the bounded execution attempt
- `required_proof_receipt`
  - exact later receipt path that records proof/reconciliation outcome
- `canonical_path_truth_checks`
  - must check whether:
    - old local path remains active
    - new local path is canonical
    - registry references are reconciled
    - current-truth surfaces are reconciled
- `stale_reference_check_scope`
  - canonical surfaces to search for stale old-path truth
- `reconciliation_allowed_scope`
  - only canonical stale references still implying the old active path may be changed
- `blocked_execution_allowed`
  - must remain `true`, because a blocked execution still yields a valid no-send proof packet for this family

## Recommended Artifact Root

If this family is later admitted into Local Data Gateway no-send packet reuse, the recommended local artifact root is:

- `runtime/gateway-packets/atlas-owned-repo-naming/<date>/<packet-id>/`

Recommended first family-specific artifacts:

- `rename-manifest.json`
- `rewrite-surface-inventory.md`
- `no-send-attestation.json`
- `proof-expectations.md`

This checkpoint does not require those artifacts to exist yet.

It only freezes their expected contract shape.

## What This Contract Enables Later

If `_stack` later reuses the Local Data Gateway chain for this family, this checkpoint would let the no-send packet chain represent:

- candidate identity without ambiguity
- exact rewrite scope without hidden path churn
- rollback posture without improvisation
- explicit no-send and no-remote assumptions
- proof/reconciliation outputs without over-reading blocked execution as success

That is the smallest useful contract slice for later adoption.

## What This Contract Still Does Not Prove

This checkpoint does not prove:

- repo naming workflows are now `adoptable now`
- generic wrapper orchestration is already enough for rename safety
- any later execution packet should be automated
- any send-capable gateway mode is needed
- any repo rename may proceed because a contract now exists

The family remains `adoptable later` until a later proof shows the current no-send chain can use this contract honestly without family-specific gateway creep.

## Exact Next Package

`Local Data Gateway repo naming rename-manifest proof-admission decision`

Why:

- the missing artifact contract is now named
- the next honest question is not broader rollout
- the next honest question is whether this contract is compact enough and stable enough to support a later proof-backed no-send admission path for the repo naming family

## Rule

Contract checkpoints must narrow future adoption cleanly without pretending the workflow already graduated to `adoptable now`.

## Pattern

bounded family stays adoptable-later -> freeze missing packet contract -> prove no-send chain can represent that contract honestly -> only then reconsider adoption graduation

## Failure Mode

A contract checkpoint gets over-read as broad Local Data Gateway rollout even though the family is still below proof-backed adoption.
