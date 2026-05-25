# Stack Lock Decision - Fitness Discord Feedback Runtime Boundary - 2026-05-25

## Decision

- `stack.lock.yaml` was not updated.

## Reason

- the `fitness` repo is still not included in `stack.yaml` under `stack_lock.include_repo_ids`
- this package changed Fitness repo source only, plus ATLAS receipts
- no stack-level lock policy change was required to record the package safely

## Package Reference

- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`

## Result

- Fitness package changes were tracked in the Fitness repo commit history
- ATLAS recorded the package receipt and this lock decision without repinning stack lock state
