# Cortex Validation Drift Classification

- Status: Resolved by explicit worktree quarantine
- Date: 2026-04-28
- Scope: Lane AA.1 drift reconciliation

## Observed Drift

Lane AA targeted verification stayed green, but stack validation moved from the accepted Cortex ambient baseline `critical=345, error=14, warning=181` to the current observed `critical=345, error=14, warning=183`.

Lane AB remains blocked while that warning drift is unresolved.

## Classification

The `warning=183` posture is classified as `current_validation_debt` until the stack owner makes an explicit registry decision.

The current receipt does not tie the warning drift to:

- `ops/cortex/connector_evidence_inventory.py`
- `tests/test_cortex_connector_evidence_inventory.py`
- `ops/cortex/lifeline_audit_index.py`
- `ops/cortex/lifeline_receipt_payload.py`
- `ops/cortex/lifeline_write_adapter.py`

## Exact Source Classification

The accepted `warning=181` warning list is not materialized as a committed receipt, so the exact delta requires inference from the current receipt plus the current stack worktree.

That inference is narrow and sufficient:

1. The current receipt includes two unrelated `unregistered-git-root` warnings for repo roots that are not represented in `stack.yaml`:
   - `repos/fawxzzy-lifeline-operator-evidence`
   - `repos/fawxzzy-trove-release-cutover`
2. The current receipt also includes an `atlas-root-path` warning at:
   - `repos/fawxzzy-trove-release-cutover/docs/lifeline-wave1-pilot.md:52`
3. The current stack worktree simultaneously removes one unrelated stack-level path leak by changing:
   - `docs/codex/FAWXZZY-FITNESS-LIVE-UI-HANDOFF-2026-04-26.md`
   - from a stack-root absolute `tmp` capture-spec path
   - to `node scripts/qa/cdp-edge.mjs tmp/captures/<capture-config>.json`

Net effect:

- `+2` unregistered repo-root warnings
- `+1` path warning from the release-cutover doc
- `-1` path warning removed from the fitness live UI handoff doc
- current net drift: `warning=181 -> warning=183`

## Posture

This drift is ambient stack-surface debt, not a Lane AA implementation regression.

It should not be silently absorbed into the accepted baseline, and it should not be used as permission to open connector-backed proof-reference generation.

## Owner Decision

The two new repo roots are not independent stack repos.

- `repos/fawxzzy-lifeline-operator-evidence` is a git worktree whose `.git` file points to `repos/fawxzzy-lifeline/.git/worktrees/fawxzzy-lifeline-operator-evidence`.
- `repos/fawxzzy-trove-release-cutover` is a git worktree whose `.git` file points to `repos/fawxzzy-trove/.git/worktrees/fawxzzy-trove-release-cutover`.

They are therefore classified as temporary trusted worktree surfaces, not canonical repo-registry members.

The stack-level fix is to quarantine them under `stack_lock.excluded_surfaces` with:

- `trust_class: trusted`
- `release_eligible: false`
- an explicit reason that they are non-canonical branch worktrees

This keeps the governed repo surface aligned with the canonical registered repos while preventing temporary worktrees from changing validation counts or export scope.

## Resolution

The chosen resolution is:

1. Do not register either worktree in `repo_registry`.
2. Do not broaden Lane AA or add connector-backed proof references.
3. Exclude both worktrees from governed repo discovery as temporary trusted worktree surfaces.
4. Leave the repo-root absolute-path example in `repos/fawxzzy-trove-release-cutover/docs/lifeline-wave1-pilot.md` untouched because that file no longer belongs to the governed validation surface after quarantine.

Expected result after the registry decision:

- stack validation returns to `critical=345, error=14, warning=181, info=0`
- Lane AB may proceed because validation posture is restored rather than silently re-baselined

## Rule

Do not open connector-backed proof-reference generation while validation-count drift is unresolved or only informally explained.

## Pattern

Treat validation-count drift as evidence to classify before increasing connector or proof power.

## Failure Mode

Do not let "not caused by this lane" become "safe to ignore."

Do not let temporary branch worktrees under `repos/` masquerade as new governed repos or contribute path-discipline warnings to Lane AA evidence.
