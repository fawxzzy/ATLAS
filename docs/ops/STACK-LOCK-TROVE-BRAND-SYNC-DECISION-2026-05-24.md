## Stack Lock Decision: Trove Brand Sync

Date: 2026-05-24

### Decision

Accept Trove commit `0f5f9fe55bd21aa7f017173f1950d0bd063470c1` as current stack truth and repin the Trove entry in `stack.lock.yaml`.

### Why

- The Trove public brand consumer targets were isolated to a seven-file package.
- `npm run verify` passed after sync.
- The package excludes Trove source work, docs and QA work, vendored Fitness icons, and unrelated consumer repos.
- Leaving `stack.lock.yaml` at the prior Trove head would create unnecessary lock drift after an accepted Trove-local package.

### Scope

This is a narrow Trove repin only.

It does not:
- regenerate the full lockfile
- change other repo pins
- change the active blocker on Fitness consumer sync visibility

### Result

`stack.lock.yaml` Trove commit moves from:

- `3a60a7cb64e4d5979988bdd444a75157bb4cfc42`

to:

- `0f5f9fe55bd21aa7f017173f1950d0bd063470c1`
