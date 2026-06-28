# ATLAS Root Stack Lock Canonical Line-Ending Guard And Validation Re-Sync

## Scope

- close the transient root-side `stack.lock.yaml` blocker without reopening any owner-repo lane
- distinguish canonical payload truth from non-canonical Windows line-ending bytes
- harden the stack-lock contract so future Windows checkouts do not reintroduce false byte drift

## Why

After the branch re-synced onto current `main`, root validation re-opened with exactly two blocking findings:

- `stack.lock.yaml`: `Stack lockfile does not match the current pinned working set.`
- `stack.lock.yaml`: `Stack lockfile bytes do not match the canonical generated lockfile payload.`

The actual payload truth was already clean. One direct comparison against `ops/stack/generate_lockfile.py` showed:

- parsed lock payload drift: `has_drift: false`
- on-disk bytes vs canonical bytes: `False`
- byte lengths: `8732` vs `8513`
- first byte difference: offset `37`, committed `CR` vs canonical `LF`

So the blocker was not a hidden repo-pin mismatch. It was Windows `CRLF` checkout drift on a file whose validator intentionally compares exact canonical bytes.

## Executed In This Pass

1. Rebuilt `stack.lock.yaml` through the canonical generator so the committed file returned to deterministic LF bytes.
2. Added one repo-root `.gitattributes` rule:
   - `stack.lock.yaml text eol=lf`
3. Added one small guard test at `tests/test_stack_lock_gitattributes.py` so future root changes cannot silently drop that policy.
4. Re-ran the root proof cluster after the lockfile rewrite and policy hardening.

## Current Truth

- `stack.lock.yaml` payload truth was already aligned with the current live working set before the rewrite
- `stack.lock.yaml` bytes are now canonical again on disk
- repo root now explicitly enforces LF checkout for `stack.lock.yaml`
- current stack validation is back at `critical=0 error=0 warning=0 info=0`
- initiative continuity manifest health remains `19 ok / 0 warning / 0 error`
- eligible open-marker restart readiness remains `7 / 7`
- the top-level dispatcher result remains `No immediate ATLAS-root packet is open`

## Consequences

- no marker ratchet is justified
- no owner-side repo truth changed
- no published clean-root checkpoint changed
- this pass only converts one fake byte-level blocker into durable lockfile hygiene

## Non-Claim

This pass does not prove:

- any new child-repo pin change
- any owner-side implementation or cleanup beyond root lockfile hygiene
- any release-readiness change for protected QA
- any new ATLAS-root packet selection beyond the existing held posture

## Verification

Commands run:

- `python ops/stack/generate_lockfile.py`
- `python -m unittest tests.test_stack_lock_gitattributes -v`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/validation/validate_stack.py`

Results:

- generator rewrote `stack.lock.yaml` with canonical bytes and preserved the same lock digest `sha256:0f6b9fc49c031c62947141b499c41afef57b6ea37d8c8886b65c36af0729cce2`
- the new `.gitattributes` guard test passes
- stack validation now reads `critical=0 error=0 warning=0 info=0`
- continuity manifest health remains `19 ok / 0 warning / 0 error`
- eligible open-marker restart readiness remains `7 / 7`
