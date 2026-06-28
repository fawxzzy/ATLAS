# ATLAS Root Repo Inventory Self-Dirty False-Positive Closeout - 2026-06-28

- Date: `2026-06-28`
- Lane: `ATLAS root`
- Mode: `root-bounded inventory truth hardening`
- Scope: `stop the published repo inventory from marking the stack root dirty solely because it rewrote its own inventory output files`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `ops/stack/export_repo_inventory.py`
  - `tests/test_stack_repo_inventory.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `codex/repo-inventory-self-dirty-fix`

## Objective

Close one exact root false-positive:

- running `ops/stack/export_repo_inventory.py` rewrites:
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
- those two writeback files were then counted as normal root dirtiness
- the published inventory could therefore report the stack root dirty because the inventory had just published itself

The required fix is narrow:

- ignore only those two exporter-owned writeback paths when computing root dirty state for the `stack` entry
- keep every other root change dirty

## Executed In This Pass

1. Added `_is_repo_dirty(...)` in `ops/stack/export_repo_inventory.py` so root dirty-state evaluation can ignore an exact allowlist of writeback paths.
2. Routed only the stack-root inventory path through that allowlist:
   - `docs/registry/STACK-REPO-INVENTORY.json`
   - `docs/audits/STACK-REPO-INVENTORY.md`
3. Added two targeted tests in `tests/test_stack_repo_inventory.py`:
   - inventory-output-only root changes keep the `stack` entry clean
   - any additional root delta still leaves the `stack` entry dirty
4. Re-exported the published inventory and reran stack validation.

## Current Truth

- the repo inventory exporter no longer treats its own two published output files as sufficient evidence that the stack root is dirty
- any other root path still keeps the stack entry dirty exactly as before
- `python -m unittest tests.test_stack_repo_inventory -v` passes, including the new self-dirty boundary tests
- `python ops/stack/export_repo_inventory.py` now publishes the current branch and commit truth without reopening stack validation
- `python ops/validation/validate_stack.py` remains `critical=0 error=0 warning=0 info=0`
- the top-level dispatcher remains `No immediate ATLAS-root packet is open`

## Honest Boundary

The current exported inventory still reports `dirty_repo_count: 1` on this live branch run.

That is honest. The remaining dirty repo at export time is not the inventory writeback itself; it is the active root implementation lane still editing exporter/test and adjacent root surfaces on branch `codex/repo-inventory-self-dirty-fix`.

This pass closes the false-positive class. It does not claim the whole root was clean at the moment of export.

## Decision

- no marker ratchet is justified
- no owner-repo truth changed
- no release-readiness state changed
- the right consequence is one bounded root hygiene closeout plus preserved current-state projection

## Verification

Commands run:

- `python -m unittest tests.test_stack_repo_inventory -v`
- `python ops/stack/export_repo_inventory.py`
- `python ops/validation/validate_stack.py`

Results:

- all six inventory tests pass, including the two new self-dirty boundary cases
- the published inventory export completes successfully with content digest `sha256:c079a4e1728d1b6212675d4b4e01404f5b6ccaaf820480071221541c62044b14`
- stack validation remains `critical=0 error=0 warning=0 info=0`
