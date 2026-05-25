# Stack Lock Decision - Fitness Discord Runtime Utility Extraction - 2026-05-25

## Decision

- `stack.lock.yaml` was not updated.

## Reason

- the Fitness repo `HEAD` changed during the Discord runtime utility extraction package
- `fitness` is not currently included in `stack.yaml#stack_lock.include_repo_ids`
- under current ATLAS lock policy, non-included repos do not trigger a stack-lock repin

## Result

- stack lock truth remains unchanged
- the package is recorded through the ATLAS receipt and the repo-local Fitness commit instead
