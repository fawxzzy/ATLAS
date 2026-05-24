## Stack Lock Decision: Trove Vendored Fitness Icons

Date: 2026-05-24

### Decision

Accept Trove commit `3a60a7cb64e4d5979988bdd444a75157bb4cfc42` as current stack truth and repin the Trove entry in `stack.lock.yaml`.

### Why

- The Trove vendored Fitness icon lane was intentionally isolated as its own package.
- The package excludes Trove source work, docs and QA work, and the remaining Trove public brand sync targets.
- `npm run verify` passed in `repos/fawxzzy-trove`.
- Leaving `stack.lock.yaml` pinned to the previous Trove head would create avoidable lock drift after an accepted Trove-local package.

### Scope

This is a narrow Trove repin only.

It does not:
- regenerate the full lockfile
- change other repo pins
- reopen the broader missing-repo constraints that still block full lock regeneration

### Result

`stack.lock.yaml` Trove commit moves from:

- `865d62e4cef9d17141971ffc3baef86fecf9ac90`

to:

- `3a60a7cb64e4d5979988bdd444a75157bb4cfc42`
