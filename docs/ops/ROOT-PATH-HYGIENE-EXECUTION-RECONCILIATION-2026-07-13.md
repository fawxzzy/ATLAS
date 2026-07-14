# Root Path Hygiene — Final Execution Reconciliation

## Identity

- Plan: `plan-07dfe809d062b89cafde`
- Cortex bridge: `root-path-hygiene-cortex-bridge-v1`
- Final audit timestamp: `2026-07-14T02:54:24Z`

## Fixed denominator and owner correlation

The historical denominator is fixed at 25 rows and was not recomputed: 16 preserved historical findings plus 9 `_stack` owner-remediation findings. `_stack` remediated all nine owner fingerprints in commit `32f9205013bbb84e19153261b1aab2c0ada975d4`, published on `_stack/main` at remote parity `0/0`.

## Final disposition

Fresh stack validation reports 19 `atlas-root-path` warnings: the 16 accepted preserved historical findings plus 3 newer findings excluded from the fixed historical denominator. All 25 target rows are accepted; pending is 0; `complete` is `true`.

The final validator summary is: 19 current warnings, 25 target rows, 25 accepted, 0 pending, 3 excluded newer, `complete: true`.

## Verification

Executed in order:

1. `python ops/validation/validate_stack.py --allow-missing-locked-repos` — completed and wrote `runtime/receipts/validation/stack-validation.latest.json`; it reports 19 `atlas-root-path` warnings and the separately tracked stack-lock error.
2. `node ops/atlas/test_validate_root_path_hygiene_disposition.mjs` — passed.
3. `node ops/atlas/validate_root_path_hygiene_disposition.mjs --registry docs/registry/ROOT-PATH-HYGIENE-DISPOSITION.v1.json --receipt runtime/receipts/validation/stack-validation.latest.json --phase final --json` — passed with the final summary above.
4. `python ops/atlas/continuity_manifest_health.py` — passed.
5. `git diff --check` — passed.

## Boundary

This receipt closes only the Root Path Hygiene child lane. Overall stack validation still has the separately tracked stack-lock error; this lane makes no claim of global stack health. Atlas Full-System Re-evaluation remains 50 percent. Cortex does not move in this job; any future Cortex marker ratchet requires its own evidence and authorization.
