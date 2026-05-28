# Atlas-Owned Repo Naming Inventory And Dependency Map - 2026-05-27

- Date: `2026-05-27`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only naming inventory / dependency map`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 50%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-EXECUTION-GATE-PASS-1-2026-05-27.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
- Control-plane checkpoint: `main@bbd2245`

## Objective

Turn the admitted naming marker into a concrete rename-safe dependency map for internal ATLAS-owned repos while preserving the explicit `fawxzzy-fitness` exception.

This pass does not:

- rename any local repo directory
- rename any remote
- assume GitHub-side rename execution
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- widen into a live rename pass

## Root State

- branch: `main`
- HEAD: `bbd2245`
- status: clean except intentional untracked `archive/`
- validation: green before dependency-map drafting at `critical=0 error=0 warning=310`

## Scope

This dependency map covers internal ATLAS-owned repo candidates that still carry `fawxzzy-` naming in their local directory names:

- `repos/fawxzzy-foundation`
- `repos/fawxzzy-lifeline`
- `repos/fawxzzy-playbook`
- `repos/fawxzzy-mazer`
- `repos/fawxzzy-stream`
- `repos/fawxzzy-trove`

Preserved exception:

- `repos/fawxzzy-fitness`

Already-canonical internal surfaces and therefore not rename candidates in this lane:

- `repos/_stack`
- `repos/DiscordOS`

Out of scope:

- adjacent unmanaged repos
- excluded recovery or worktree residue names
- archive and zip surfaces

## Canonical Target Naming Rule

Desired internal canonical names strip the unnecessary `fawxzzy-` prefix while keeping the stable logical repo ids already used in the stack registry.

Target local names:

- `repos/fawxzzy-foundation` -> `repos/foundation`
- `repos/fawxzzy-lifeline` -> `repos/lifeline`
- `repos/fawxzzy-playbook` -> `repos/playbook`
- `repos/fawxzzy-mazer` -> `repos/mazer`
- `repos/fawxzzy-stream` -> `repos/stream`
- `repos/fawxzzy-trove` -> `repos/trove`

Explicit preserved exception:

- `repos/fawxzzy-fitness` stays as-is for now

## Canonical Control-Plane Surfaces In Active Use

The current naming dependency footprint is concentrated in these canonical ATLAS-root surfaces:

- stack registry:
  - `stack.yaml`
  - `stack.lock.yaml`
- repo inventory and truth-map publication:
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
- system-map and restart surfaces:
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- lane doctrine and receipt spine:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-EXECUTION-GATE-PASS-1-2026-05-27.md`
  - `docs/atlas-book/05-receipt-index.md`

These are the surfaces that must be treated as canonical current-truth rewrite scope before any future local rename lane opens.

## Candidate Inventory And Dependency Map

| Logical id | Current local directory | Desired canonical internal name | Stack registry references | Receipt / restart / truth-map references | Possible remote-name dependency | Local rename-safe later? | Current classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `foundation` | `repos/fawxzzy-foundation` | `repos/foundation` | `stack.yaml`, `stack.lock.yaml`, repo inventory JSON/MD | system map, naming doctrine receipts | remote currently `https://github.com/fawxzzy/fawxzzy-foundation.git`; future local rename must not assume remote rename | appears feasible later: clean repo, `main`, no manifest-backed restart surface of its own found here | `rename-safe candidate later` |
| `lifeline` | `repos/fawxzzy-lifeline` | `repos/lifeline` | `stack.yaml`, `stack.lock.yaml`, repo inventory JSON/MD | naming doctrine receipts | remote currently `https://github.com/fawxzzy/fawxzzy-lifeline.git`; remote-name assumption remains prohibited | not yet safely classed for execution because current branch is non-`main` and repo is dirty in lock/inventory | `blocked by dependency mapping gap` |
| `playbook` | `repos/fawxzzy-playbook` | `repos/playbook` | `stack.yaml`, `stack.lock.yaml`, repo inventory JSON/MD | naming doctrine receipts | remote currently `https://github.com/fawxzzy/fawxzzy-playbook.git`; remote-name assumption remains prohibited | not yet safely classed for execution because current branch is non-`main` and repo is dirty in lock/inventory | `blocked by dependency mapping gap` |
| `mazer` | `repos/fawxzzy-mazer` | `repos/mazer` | `stack.yaml`, `stack.lock.yaml`, repo inventory JSON/MD | system map, inventory surfaces | remote currently `https://github.com/fawxzzy/fawxzzy-mazer.git`; remote-name assumption remains prohibited | appears feasible later, but current branch is non-`main`; execute only after branch-state review | `rename-safe candidate later` |
| `stream` | `repos/fawxzzy-stream` | `repos/stream` | `stack.yaml`, `stack.lock.yaml`, repo inventory JSON/MD | naming doctrine receipts | no configured remote in `stack.lock.yaml`; this reduces remote-rename pressure but does not remove registry rewrite scope | appears feasible later: clean repo, `main`, lighter outward dependency footprint | `rename-safe candidate later` |
| `trove` | `repos/fawxzzy-trove` | `repos/trove` | `stack.yaml`, `stack.lock.yaml`, repo inventory JSON/MD | system map, naming doctrine receipts | remote currently `https://github.com/fawxzzy/fawxzzy-trove.git`; remote-name assumption remains prohibited | appears feasible later, but current branch is non-`main`; execute only after branch-state review | `rename-safe candidate later` |
| `fitness` | `repos/fawxzzy-fitness` | preserved as `repos/fawxzzy-fitness` | `stack.yaml`, repo inventory JSON/MD | system map, current-state, restart surfaces, many Discord/Fitness lane receipts | remote currently `https://github.com/fawxzzy/fawxzzy-fitness.git`, but this lane must not touch it | intentionally not a rename target in this lane | `preserved exception` |

## Why Some Candidates Are Only “Later” Safe

`rename-safe candidate later` does not mean execution-approved now.

It means the candidate currently appears small enough and local enough that a future bounded rename lane could plausibly open after:

- stack registry rewrite plan is explicit
- restart-surface rewrite plan is explicit
- rollback steps are explicit
- current branch and dirty-state posture are rechecked at execution time

That is the strongest honest classification this pass can give without silently converting mapping work into approval.

## Why Some Candidates Stay Blocked

The blocked candidates are not blocked because the target names are wrong.

They are blocked because their current live repo state would add rename risk on top of the still-required registry rewrite:

- `lifeline`
  - dirty in the current lock/inventory
  - active non-`main` branch
- `playbook`
  - dirty in the current lock/inventory
  - active non-`main` branch

Those are not permanent blockers.

They are current execution blockers until a future rename lane verifies candidate-local safety again.

## Shared Dependency Map Rules

Every future rename candidate in this lane inherits the same hard dependency families:

### 1. Stack Registry Rewrite Scope

Must be rewritten together:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`

### 2. Truth-Map And Restart Scope

Must be checked and rewritten where current-truth naming is displayed:

- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

### 3. Naming Doctrine Receipt Scope

Must be checked so the naming-governance lane stays historically coherent:

- `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
- `docs/ops/ATLAS-OWNED-REPO-NAMING-EXECUTION-GATE-PASS-1-2026-05-27.md`
- future naming execution receipts

### 4. Remote-Name Assumption Scope

Must remain blocked by default:

- local directory rename is not GitHub remote rename
- remote URLs may remain prefixed even after any future local canonicalization
- no receipt may imply remote churn unless a separate remote lane is explicitly opened

## Honest Candidate Read

Current honest candidate read:

- `rename-safe candidate later`
  - `foundation`
  - `mazer`
  - `stream`
  - `trove`
- `blocked by dependency mapping gap`
  - `lifeline`
  - `playbook`
- `preserved exception`
  - `fitness`

This does not mean the four “later” candidates are ready now.

It means they currently look tractable once the already-admitted execution gates are opened with explicit rollback and rewrite sequencing.

## What This Pass Does Not Approve

This pass does not approve:

- any local repo rename
- any remote rename
- any GitHub-side rename
- any owner-repo content rewrite
- any weakening of the `fawxzzy-fitness` exception

Execution remains blocked until a future lane freezes:

- exact rewrite order
- exact rollback order
- exact candidate subset

## Marker Interpretation

This pass strengthens the naming lane materially.

It does not justify a marker move by itself unless a later ratchet pass explicitly recomputes that effect.

Why:

- the dependency map is now durable
- candidate-local differences are now explicit
- remote-name assumptions remain blocked
- execution is still not open

## Exact Next Package

`Atlas-owned Repo Naming Canonicalization marker ratchet checkpoint 2`

Why:

- the lane now has durable policy
- durable execution gates
- and now a durable rename-safe dependency map with per-candidate classification
- the next honest move is to recompute whether that justifies a small marker move without implying execution approval

## Rule

Naming inventory must map rename dependencies before any execution lane opens.

## Pattern

policy admission -> execution gate -> dependency map -> marker ratchet -> bounded rename sequence

## Failure Mode

A naming cleanup lane pretends all prefixed repos are equally safe to rename.
