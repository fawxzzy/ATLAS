# ATLAS Guarded Continuation Gate Prompt

## Objective

Return one machine-readable ATLAS continuation result for the just-finished bounded Codex slice so `ops/codex/atlas_continue_gate.py` can decide whether automatic continuation is still honest.

## Output Contract

Return one JSON object only. Do not wrap it in Markdown. Use the schema:

- `ops/codex/schemas/atlas_codex_result.schema.json`

Required fields:

- `contract_version`
- `result_id`
- `generated_at`
- `producer`
- `lane_id`
- `active_slice`
- `summary`
- `changed_files`
- `decisive_receipt_path`
- `validation_snapshot`
- `marker_outcome`
- `next_move`
- `scope_guard`

## Required Truth Rules

- `changed_files` must list exact ATLAS-relative paths only.
- `decisive_receipt_path` must be ATLAS-relative when a receipt was created.
- `validation_snapshot` must report the exact validator posture already observed, not an inferred or aspirational posture.
- `marker_outcome.items` must report exact marker movement or explicit `none`.
- `next_move.package` must be one exact next packet, or one exact `none ...` statement if continuation should stop.
- `next_move.mode` must reflect the honest execution path for the next move, such as `Codex` or `Normal Chat`.
- `scope_guard.widened_scope` must be `true` if the slice opened new family scope, reopened held lanes, or widened beyond the admitted packet.
- `scope_guard.non_automated_attempted` must list any attempted doctrine admission, deploy judgment, publication judgment, destructive cleanup, secret approval, or ambiguous review.
- `scope_guard.out_of_scope_admissions` must list any new admitted lane or family that was not part of the bounded slice.

## Guard Semantics

The continuation gate will stop if any of these are true:

- validator posture worsened beyond admitted dirty-state drift
- `next_move.package` is missing or starts with `none`
- `next_move.mode` is not `Codex`
- scope widened
- held lanes were not preserved
- any explicitly non-automated class was attempted
- marker movement was reported without explicit justification

## Forbidden Output Behavior

- no Markdown fences
- no prose outside the JSON object
- no absolute paths
- no invented receipt paths
- no invented validator snapshot
- no claiming marker movement unless this slice actually changed operator reality
