# Atlas-Owned Repo Naming Canonicalization - 2026-05-27

- Date: `2026-05-27`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only marker admission / naming-governance pass`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 50%`
- Source surfaces:
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `stack.yaml`
  - `README-STACK.md`
- Control-plane checkpoint: `main@8017f8f`

## Objective

Admit a new canonical percent marker that tracks whether ATLAS-owned internal stack repos converge toward singular canonical names without unnecessary legacy `fawxzzy-` prefixes.

This pass does not:

- rename any live repo directory
- rename any remote
- assume GitHub rename execution
- rename `fawxzzy-fitness`
- change repo ownership
- mutate runtime or deployment surfaces

## Root State

- branch: `main`
- HEAD: `8017f8f`
- status: clean except intentional untracked `archive/`
- validation: green before marker admission at `critical=0 error=0 warning=310`

## Marker Meaning

`Atlas-owned Repo Naming Canonicalization` tracks whether internal ATLAS-owned repos have:

- clear singular canonical directory names
- explicit exception handling where a legacy or externally meaningful name is intentionally preserved
- control-plane references that can survive rename execution safely later

This is a naming-governance and migration-readiness lane first.

It is not a live rename lane yet.

## Explicit Exception

Keep `fawxzzy-fitness` as-is for now.

Reason:

- Fitness remains the externally meaningful pilot/product repo name
- the current stack and rollout surfaces still rely on that identity
- this naming lane should not create accidental product, remote, or workflow ambiguity by forcing Fitness into the same policy bucket as internal stack-owned repos

## Scope

This marker covers:

- internal ATLAS-owned stack repos only
- repo directory naming
- stack registry and truth-map references
- restart-surface naming references
- migration-safe rename sequencing

This marker does not cover:

- external or intentionally preserved product names
- remote rename execution
- GitHub repository rename policy
- adjacent unmanaged repos
- archive/quarantine residue names

## In-Scope Internal Repo Set

Current internal ATLAS-owned naming set:

- `_stack`
- `DiscordOS`
- `repos/fawxzzy-foundation`
- `repos/fawxzzy-lifeline`
- `repos/fawxzzy-playbook`
- `repos/fawxzzy-mazer`
- `repos/fawxzzy-stream`
- `repos/fawxzzy-trove`

Explicit exception set:

- `repos/fawxzzy-fitness`

Explicitly out of scope for this lane:

- `repos/Nat1-Games`
- `repos/playbook-demo`
- `repos/ZachariahRedfield`
- excluded surfaces and quarantined archive names

## Non-Goals

- no live rename execution in this pass
- no GitHub remote rename assumptions
- no filesystem migration
- no receipt rewrite campaign
- no silent registry/path churn
- no owner-transfer implication

## Scoring Rubric

- `0%`
  - naming is still mostly legacy or inconsistent
  - no durable policy exists
- `25%`
  - naming policy is discussed
  - scope is still fuzzy or exceptions are not frozen
- `50%`
  - canonical naming policy is durable
  - explicit exceptions are durable
  - the internal inventory is clear enough to support future migration planning
- `75%`
  - rename-safe execution plan exists
  - dependent control-plane surfaces are mapped
  - sequencing and rollback posture are explicit
- `100%`
  - internal repo names and control-plane references are canonicalized
  - no regression was introduced across registry, restart, receipt, or owner-routing surfaces

## Current Assessment

Current internal naming posture is mixed:

- some internal repos already use canonical singular names:
  - `_stack`
  - `DiscordOS`
- several internal repos still carry legacy `fawxzzy-` prefixes:
  - `fawxzzy-foundation`
  - `fawxzzy-lifeline`
  - `fawxzzy-playbook`
  - `fawxzzy-mazer`
  - `fawxzzy-stream`
  - `fawxzzy-trove`
- the Fitness name remains intentionally preserved by exception

That means the lane is not near execution complete.

But after this pass it is no longer policy-ambiguous.

## Honest Marker Position

Set the marker at `50%`.

Why:

- the naming-governance rule is now explicit
- the internal target set is explicit
- the Fitness exception is explicit
- the lane now has a durable policy baseline for later migration-safe planning

Why it is not higher:

- no rename-safe dependency map is frozen yet
- no restart-surface impact review is complete yet
- no registry or remote sequencing plan exists yet
- no rollback or no-regression rename plan exists yet

## Migration-Safe End State

The intended end state is:

- internal ATLAS-owned stack repos converge toward singular/internal canonical names
- control-plane references follow that naming safely
- explicitly preserved exceptions remain explicit instead of accidental

The intended end state is not:

- broad cosmetic churn
- surprise remote rename execution
- product-identity erosion

## Exact Next Package

`Atlas-owned repo naming canonicalization inventory and dependency map`

Why:

- the next honest move is not rename execution
- the next honest move is to map dependent surfaces first:
  - stack registry
  - lock projections
  - restart surfaces
  - receipt conventions
  - owner-routing docs

## Rule

Naming canonicalization must freeze policy and migration safety before any rename execution.

## Pattern

marker admission -> durable policy -> explicit exceptions -> dependency map -> rename-safe sequencing -> execution

## Failure Mode

A naming cleanup lane turns into immediate live renames without registry, remote, or receipt impact mapping.
