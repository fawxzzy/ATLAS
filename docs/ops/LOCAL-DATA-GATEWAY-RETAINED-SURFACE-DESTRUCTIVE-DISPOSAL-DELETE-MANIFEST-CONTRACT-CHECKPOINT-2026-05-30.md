# Local Data Gateway Retained-Surface Destructive Disposal Delete-Manifest Contract Checkpoint - 2026-05-30

- Date: `2026-05-30`
- Owner: ATLAS root
- Mode: `docs-only delete-manifest contract checkpoint`
- Scope: `retained-surface destructive disposal packet family only`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-INVENTORY-PASS-1-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-EXPANSION-PASS-2-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-BROADER-ADOPTION-CANDIDATE-SELECTION-AND-PACKET-ADMISSION-PASS-2-2026-05-30.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PACKET-CONTRACT-DRAFT-2026-05-27.md`
  - `docs/ops/RETAINED-SURFACE-MANUAL-DISPOSAL-PASS-2026-05-27.md`
  - `docs/ops/RETAINED-SURFACE-REGISTRY-HYGIENE-REVIEW-2026-05-27.md`
  - `runtime/receipts/validation/stack-validation.latest.md`

## Objective

Freeze the smallest honest `delete-manifest` contract for Local Data Gateway retained-surface destructive disposal packets without reopening destructive execution, send-capable behavior, owner-side implementation, or shared restart-spine work.

This checkpoint does not:

- authorize deletion
- reopen retained-surface manual disposal execution
- reopen registry-hygiene reconciliation as a packet family
- widen Local Data Gateway into destructive approval or send behavior
- claim the retained-surface destructive disposal family is now `adoptable now`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- working tree: dirty from surrounding Wave work outside this packet
- validation before drafting: `critical=0 error=3 warning=489 info=0`

## Durable Starting Truth

The retained-surface destructive disposal family was admitted for one exact contract checkpoint because the remaining gap was contract-shaped, not implementation-shaped:

- the family already uses bounded candidate sets
- the family already uses exact delete scopes
- the family is still `adoptable later`
- the three missing maturity classes were already frozen as:
  - no delete-manifest contract
  - no explicit packet-review-to-delete-approval relationship
  - no proof that Local Data Gateway improves safety before deletion

This checkpoint addresses only the first missing maturity class.

## Exact Delete-Manifest Contract Surface

The Local Data Gateway `delete-manifest` is now frozen as a local review packet that describes an exact proposed destructive subset without authorizing or executing disposal.

Its contract surface is:

- one packet artifact per bounded retained-surface disposal subset
- one exact proposed delete set only
- one explicit non-delete bucket for nearby retain, manual-review, blocked, or unknown candidates
- one evidence-backed rationale trail for every path named in the proposed delete set
- one explicit truth-limit section stating that the manifest is a review artifact, not execution authority

The manifest may describe:

- which exact paths are proposed for deletion
- why each path is classed as delete-candidate, retain, manual-review, or blocked
- what evidence surfaces support each classification
- what review state exists locally
- what destructive approval still remains missing

The manifest may not describe itself as:

- a delete command
- a mutation request
- an execution receipt
- an approval artifact by itself
- proof that a path is safe to remove without later review

## Required Delete-Manifest Fields

Every retained-surface destructive disposal `delete-manifest` must include:

- `packet_purpose`
- `packet_schema_version`
- `downstream_target_class`
- `sensitivity_label`
- `source_provenance`
- `transformation_record`
- `validation_result`
- `redaction_status`
- `dedupe_status`
- `minimal_useful_payload`

And the family-specific required fields are now frozen as:

- `candidate_family`
- `manifest_scope`
- `proposed_delete_set`
- `non_delete_set`
- `classification_basis`
- `review_state`
- `destructive_approval_state`
- `truth_limits`
- `receipt_refs`

## Field Meanings For This Family

### `candidate_family`

Must be:

- `retained-surface-destructive-disposal`

### `manifest_scope`

Must state:

- the exact bounded disposal subset under review
- whether the scope is path-exact or parent-scope-exact
- whether nearby same-class candidates were inspected but excluded

### `proposed_delete_set`

Must list only exact path entries proposed for deletion and, for each entry:

- path
- current class
- decision label
- supporting receipt refs
- whether the scope is exact-path or parent-path inclusive

### `non_delete_set`

Must list nearby or related candidates that were intentionally not admitted into `proposed_delete_set` and why:

- `retain`
- `manual-review`
- `blocked`
- `unknown-dependency`

### `classification_basis`

Must record the local evidence basis used for each class:

- exact prior durable receipt support
- bounded local presence or absence observation
- worktree or owner-surface status only when already cited from durable evidence or current local read

### `review_state`

Must state only review posture, not authority:

- `candidate-shaped`
- `reviewed-locally`
- `awaiting-destructive-approval-link`
- `not-approved-for-delete`

### `destructive_approval_state`

Must remain one of:

- `missing`
- `explicitly-linked`

For this family at this checkpoint, the honest default remains:

- `missing`

unless a later bounded packet freezes the approval relationship explicitly.

### `truth_limits`

Must state that the manifest:

- is local-only
- is reviewable
- is non-executing
- does not authorize destructive disposal
- does not convert review into delete approval

## Retained-Surface Destructive Disposal Family Boundaries

This family includes:

- exact retained-surface delete candidates
- exact nearby same-class candidates that require non-delete classification
- cited review receipts that classify a surface as disposable, retained, or manual-review
- local packetization of that classification into one bounded review manifest

This family does not include:

- registry-hygiene reconciliation receipts whose value is direct canonical truth correction
- marker ratchets
- doctrine receipts
- send-capable handoff
- destructive execution
- owner-side implementation

## Admitted Disposal Evidence Classes

The `delete-manifest` may admit only these evidence classes:

### 1. Durable disposal subset receipts

Examples:

- exact approved delete sets
- exact removed-path inventories
- explicit non-delete candidate tables

### 2. Durable governance classification receipts

Examples:

- `evidence retain`
- `safety-checkpoint retain`
- `manual-review retain`
- `unknown-dependency retain`

### 3. Local current-state observations

Allowed only as bounded observational facts such as:

- path exists or is absent
- path is within the exact scoped candidate set
- nearby same-class sibling exists

These observations may support classification packaging but may not self-authorize deletion.

### 4. Durable review/provenance refs

Allowed only as cited supporting refs that explain why a path entered or stayed out of the proposed delete set.

## Forbidden Disposal Evidence Classes

The `delete-manifest` may not admit:

- uncited delete safety inference
- secret or protected-surface material
- owner-side runtime truth
- send-capable target routing
- destructive execution results as approval substitute
- broad sibling expansion beyond the exact scoped candidate family
- registry-hygiene prose as if it were destructive approval
- packet review language that collapses into delete authority

## Explicit Relationship To Destructive Approval

The relationship is now frozen as:

- `delete-manifest` packages candidate truth
- `delete-manifest` does not grant destructive approval
- any future delete approval must cite the manifest, not be implied by it
- any future execution receipt must cite both the manifest and the later approval relationship packet

This checkpoint therefore narrows the family ambiguity but does not clear the destructive-approval blocker.

## Recommendation Status

Recommendation type:

- `durable`

Why:

- the contract is anchored in already-frozen Local Data Gateway adoption receipts and retained-surface disposal receipts
- no speculative implementation assumption is required to define the bounded review-manifest shape

## Marker Decision

Decision:

- hold `Local Data Gateway` flat

Why:

- this checkpoint freezes one missing contract only
- it does not widen the proven `adoptable now` set
- it does not prove that Local Data Gateway improves safety before deletion
- it does not admit destructive approval or execution

## Validation

- `python .\ops\validation\validate_stack.py`
- result after drafting: `critical=0 error=3 warning=489 info=0`

The live `error=3` state remains the already-classified in-flight `stack.lock.yaml` dirty-state drift and is not introduced by this receipt.

## Exact Next Packet

- `Local Data Gateway retained-surface destructive disposal packet-review-to-delete-approval relationship checkpoint`

Why:

- the `delete-manifest` contract is now frozen
- the next unresolved family blocker is the explicit relationship between packet review and destructive approval
- safety proof before deletion still cannot widen honestly until that relationship is frozen

## Rule

Delete-manifest packetization may narrow destructive review ambiguity, but it may not impersonate delete authority.

## Pattern

bounded destructive candidate family -> exact review manifest contract -> explicit approval relationship checkpoint -> safety-improvement proof only after both are frozen

## Failure Mode

The delete-manifest looks tidy enough that later packets quietly treat it as authorization, collapsing review packaging into destructive approval without ever freezing the missing relationship explicitly.
