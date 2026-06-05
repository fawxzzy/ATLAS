# Stack Validation Validator-Correctness Warning-Burn Pass 1

Date: 2026-06-05
Branch: `codex/root-path-discipline-warning-slice-1`

## Scope

Bounded root-side validator correctness slice only.

No owner-repo source was edited.

Explicit non-scope:

- `repos/fawxzzy-fitness`
- `archive/`
- stack-lock refresh
- Vercel linkage mutation
- repo-local secret deletion

## Why This Pass Was Admitted

The remaining non-Fitness warning surface had narrowed enough that the next honest move was validator correction, not more blind residue deletion.

Two concrete false-positive behaviors were active:

1. `.env.example`-style files were still being classified as `repo-local-secret-material`.
2. overlapping root log glob patterns could emit duplicate warnings for the same file path.

## Changes

Changed `ops/validation/validate_stack.py`:

- `ENV_EXAMPLE_MARKERS` now models suffix tokens instead of dotted substring fragments.
- `is_repo_local_secret_candidate(...)` now correctly exempts `.env.example`, `.env.sample`, `.env.template`, `.env.dist`, and chained forms like `.env.local.example`.
- added `iter_unique_repo_root_files(...)` so overlapping root-artifact glob patterns do not double-count the same file.
- root mutable-artifact and capture scans now use the deduped iterator.

Added focused regression proof at `tests/validation/test_validate_stack_mutable_state_rules.py`:

- example env variants are not secret candidates
- direct env surfaces still are
- overlapping root log patterns dedupe to one finding per file path

## Verification

- `python -m unittest tests.validation.test_validate_stack_mutable_state_rules -v`
  - `2 tests OK`
- `python -m py_compile ops\validation\validate_stack.py tests\validation\test_validate_stack_mutable_state_rules.py`
  - passed
- `python .\ops\validation\validate_stack.py --ratchet`
  - `critical=0 error=16 warning=57 info=0`

## Result

Warning count moved from `59` to `57` without touching Fitness or widening scope.

The two removed warnings were:

- duplicate `mutable-artifact-in-repo-root` emission for `repos/fawxzzy-fitness/tmp-dev-server.err.log`
- false `repo-local-secret-material` emission for `repos/stream/.env.example`

The remaining `16` errors are unchanged stack-lock drift across active owner branches and are not part of this pass.

## Next Honest Move

Continue warning reduction only through one of these explicit routes:

1. additional validator-correctness fixes if another false-positive class is evidenced
2. deliberate owner-side cleanup of tracked mutable-state surfaces outside Fitness
3. stack-lock refresh / owner-branch preservation if the blocker class being addressed is lock drift rather than warning debt
