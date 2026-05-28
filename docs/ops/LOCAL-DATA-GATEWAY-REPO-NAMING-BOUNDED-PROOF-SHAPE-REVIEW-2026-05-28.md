# Local Data Gateway Repo Naming Bounded Proof-Shape Review - 2026-05-28

- Date: `2026-05-28`
- Owner: ATLAS root
- Mode: `docs-only proof-shape review`
- Scope: `repo naming rename-manifest bounded proof class inside Local Data Gateway`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-RENAME-MANIFEST-CONTRACT-CHECKPOINT-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-RENAME-MANIFEST-PROOF-ADMISSION-DECISION-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-EXPANSION-PASS-2-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-PROOF-PASS-1-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-AUTHORIZATION-PREREQUISITES-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-STREAM-BLOCKER-DISPOSITION-RATCHET-2026-05-28.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@7ae6bf2`

## Objective

Freeze the exact proof-shape expectations for the repo-naming rename-manifest class now that it is durable as `proof-admitted later`, without promoting it to `adoptable now`.

This review does not:

- modify `_stack`
- imply send-capable behavior
- authorize repo rename execution
- authorize remote or GitHub-side rename assumptions
- graduate repo naming into `adoptable now`
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `7ae6bf2`
- status: clean except intentional untracked `archive/`
- validation: green before drafting at `critical=0 error=0 warning=310`

## Current Repo-Naming Posture Inside Local Data Gateway

The repo-naming family remains:

- `proof-admitted later`
- `contract-complete but execution-blocked`

That means:

- the family is above plain `adoptable later`
- the family is below `adoptable now`
- the no-send chain may later package bounded proof for this family
- the no-send chain may not yet be treated as a generic admitted execution surface for this family

## Review Standard

For the bounded proof shape to be honest, it must:

1. preserve the already-frozen rename-manifest contract
2. admit both blocked and successful local execution truth
3. keep all transport and send semantics explicitly out of scope
4. produce proof outputs that remain useful even when the rename does not execute
5. avoid adding gateway-specific rename execution logic by implication

If any of those fail, the family falls back to undifferentiated `adoptable later`.

## Bounded Proof Class Under Review

The bounded proof class is:

- local-only rename-manifest proof packets for Atlas-owned repo naming candidates

The proof class may package:

- candidate identity
- rewrite-surface inventory
- rollback order
- no-send attestation
- blocked-before-rename truth
- executed-and-reconciled truth

The proof class may not package:

- remote rename execution
- GitHub-side rename execution
- send-capable handoff
- generic multi-family execution semantics
- target selection or transport behavior

## Minimum Required Manifest Fields

Any packet presented as this proof class must include, at minimum:

1. `candidate_identity`
2. `rewrite_surface_inventory`
3. `rollback_order`
4. `no_send_attestation`
5. `proof_reconciliation_expectations`

Those sections are not optional.

The family remains below admission if any packet drops one of them or collapses them into narrative prose.

### Minimum internal field expectations

`candidate_identity` must still name:

- `lane`
- `candidate_id`
- `source_local_path`
- `target_local_path`
- `candidate_class`
- `approval_receipt`
- `rewrite_plan_receipt`
- `current_marker_posture`
- `exception_boundary`

`rewrite_surface_inventory` must still name:

- one exact local directory rename
- canonical registry surfaces
- canonical inventory surfaces
- current-truth surfaces
- receipt-index surfaces
- expected no-op checks
- historical receipt rewrite rule

`rollback_order` must still name:

- rollback trigger conditions
- reverse-ordered rollback steps
- validation command
- explicit rollback scope limit

`no_send_attestation` must still name the currently prohibited transport and remote-assumption fields.

`proof_reconciliation_expectations` must still name:

- execution outcome class
- required execution receipt
- required proof receipt
- canonical path truth checks
- stale-reference search scope
- reconciliation allowed scope
- blocked execution allowance

## Acceptable `blocked-before-rename` Proof

The proof class remains valid when the rename does not execute, if all of the following are true:

1. the execution receipt explicitly records `blocked-before-rename`
2. the blocker class is exact and durable
3. the old local path is still proven active
4. the new local path is still proven absent or non-canonical
5. registry and current-truth surfaces are proven intentionally unchanged rather than forgotten
6. no remote-name assumption was introduced

Minimum acceptable blocked proof bundle:

- one rename-manifest packet naming the exact candidate
- one execution receipt showing the blocked precondition
- one proof/reconciliation receipt confirming:
  - old path still canonical
  - new path not yet canonical
  - current canonical references to the old path are therefore not stale
- one no-send attestation holding all remote-facing fields at `false`

Blocked proof is valid for this family because blocked state is part of the contract, not a contract failure.

## Acceptable `executed-and-reconciled` Proof

The proof class remains valid when the rename does execute, if all of the following are true:

1. the execution receipt explicitly records one exact local rename
2. the rename follows the frozen rewrite order
3. registry surfaces are reconciled
4. canonical inventory and current-truth surfaces are reconciled
5. stale old-path references are searched across the allowed canonical scope
6. only genuinely stale canonical references are rewritten
7. no remote-name assumption was introduced
8. validation is green after reconciliation

Minimum acceptable executed proof bundle:

- one rename-manifest packet naming the exact candidate
- one execution receipt recording the bounded local rename
- one proof/reconciliation receipt confirming:
  - old path no longer represents active local truth
  - new path is now canonical local truth
  - registry references are reconciled
  - canonical current-truth surfaces are reconciled
  - stale-reference search stayed inside the allowed canonical scope
- one no-send attestation holding all remote-facing fields at `false`
- one validation result reference

## No-Send Attestation Expectations

The proof class stays inside Local Data Gateway only if all of the following remain explicitly `false`:

- `downstream_send_performed`
- `downstream_execution_performed`
- `remote_target_selected`
- `automatic_handoff_authorized`
- `remote_name_assumed`
- `github_name_assumed`
- `owner_repo_runtime_mutation_performed`

Required narrative boundary:

- the packet is a local control-plane artifact only
- review or proof packaging does not authorize execution
- blocked and executed proof outcomes are still local-only evidence products
- no packet review state may be over-read as send, sync, post, submit, mutate, or rename authority

## Proof / Reconciliation Output Expectations

The bounded proof class should produce or point to these local outputs:

1. `rename-manifest.json`
2. `rewrite-surface-inventory.md`
3. `no-send-attestation.json`
4. `proof-expectations.md`
5. exact execution receipt reference
6. exact proof/reconciliation receipt reference
7. validation result reference

Receipt-ready summary output must state:

- candidate id
- execution outcome class
- whether proof is blocked-state or executed-state
- whether canonical references changed
- whether validation stayed green
- whether all no-send fields remained `false`

## Why This Still Stops Below `adoptable now`

This review sharpens the proof class.

It does not graduate the family.

The family still stays below `adoptable now` because:

- the current useful outcome is still tightly coupled to rename-lane execution state
- the current generic no-send chain is not yet proven to carry this family without rename-specific gateway logic
- the active `stream` candidate remains execution-blocked by owner-side worktree blockers
- no family-wide proof yet shows reuse across more than one bounded candidate packet shape

## Relation To The Current `stream` Packet

The current `stream` packet is a valid example of why this proof class is useful but not yet adopted.

It shows:

- a contract-complete candidate packet
- one honest blocked execution chain
- one honest blocked proof / reconciliation chain
- one case where blocked truth is still a meaningful local proof product

It does not show:

- admitted execution automation
- generic gateway reuse beyond the family-specific contract
- multi-candidate proof portability

## What This Pass Proves

This pass proves:

- the repo-naming family now has a frozen bounded proof shape
- blocked-before-rename and executed-and-reconciled are both valid proof outcomes
- no-send attestation for this family is now explicit enough to review without overclaiming execution
- the family remains a bounded Local Data Gateway proof posture, not an adopted execution posture

## What This Pass Does Not Prove

This pass does not prove:

- repo naming is now `adoptable now`
- `_stack` should implement repo-naming packet logic next
- any rename candidate may execute because the proof shape is clear
- any remote, GitHub, or send-capable surface is now admissible
- any marker move for `Local Data Gateway`

## Exact Next Package

`Local Data Gateway marker ratchet checkpoint 10`

Why:

- the repo-naming family now has contract checkpoint, proof admission, and bounded proof-shape review
- the next honest question is whether that is enough to move `Local Data Gateway` beyond `65%` by the smallest honest amount
- that question still stays below implementation, send behavior, and adopt-now graduation

## Rule

Proof-shape review must narrow the evidence class cleanly without silently graduating execution-blocked workflows into adopt-now.

## Pattern

family stays adoptable-later -> freeze manifest contract -> admit bounded proof class -> freeze proof shape -> only then reconsider lane maturity

## Failure Mode

A bounded proof class gets over-read as operational adoption just because the contract and evidence vocabulary are now strong.
