# Dependency Untangling Blocker-Family Compression Pass 2 - 2026-05-29

- Date: `2026-05-29`
- Lane: `Dependency Untangling blocker-family compression pass 2`
- Mode: `docs-only root-bounded ladder compression`
- Source surfaces:
  - `docs/ops/STACK-LANE-0-TRUTH-MAP-2026-05-22.md`
  - `docs/ops/POST-CONVERGENCE-LANE-SPLIT-READINESS-2026-05-24.md`
  - `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
  - `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
  - `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`
  - `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-PLAN-2026-05-24.md`
  - `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
  - `docs/ops/DEPENDENCY-UNTANGLING-DECISIVE-RECEIPT-AND-BLOCKED-WORK-LADDER-SHAPING-PASS-1-2026-05-29.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-CONTINUITY-MANIFEST-REFRESH-PASS-4-2026-05-29.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Compress the current four-family `Dependency Untangling` blocked-work ladder into the smallest honest exact next blocker family without performing the untangling work itself.

This pass does not:

- move code
- mutate repos
- create runtime, schema, or Vercel state
- execute the chosen family
- change owner boundaries
- move the marker

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status: shared root spine already dirty from adjacent durable work; this pass stays within bounded restart and continuity surfaces
- validation: green before compression at `critical=0 error=0 warning=478`

## Ladder Before Compression

The shaped lane entered this pass with four explicit blocker families:

1. `shared-contract seam dependency family`
2. `env/runtime ownership dependency family`
3. `runtime cutover dependency family`
4. `repo bootstrap and extraction dependency family`

The question for this pass was not which family is most interesting.

It was which family now has the strongest decisive receipt support, blocked-work specificity, and next-package specificity, while still sitting upstream of the rest.

## Four-Family Evaluation

### 1. Shared-contract seam dependency family

- decisive receipt support:
  - `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- blocked-work specificity:
  - explicit seam-by-seam blocker classes are already named:
    - verification bridge
    - `discord_member_links`
    - member-number sync
    - deploy-to-update handoff
    - shared ids / immutable keys
- next-package specificity:
  - the receipt already names the first safe migration order and routes directly into later env, schema, and runtime packages
- restart-compressible now:
  - yes

Why it is strongest:

- it is the earliest upstream dependency gate
- the later families depend on these seams being explicit before their own execution can become honest
- its decisive receipt already names the follow-on package order rather than describing a broad future state only

### 2. Env/runtime ownership dependency family

- decisive receipt support:
  - `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
- blocked-work specificity:
  - strong owner-class mapping exists for env, runtime, bot, Supabase, and Vercel classes
- next-package specificity:
  - strong, but it routes forward only after the contract seam posture is already accepted
- restart-compressible now:
  - partially, but still downstream of the seam family

Why it does not win:

- it is better mapped than the later families, but it still depends on the seam family being the canonical first execution-adjacent boundary
- it clarifies ownership classes; it does not outrank the seam contracts that those ownership classes must protect

### 3. Runtime cutover dependency family

- decisive receipt support:
  - `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`
- blocked-work specificity:
  - strong cutover stages and rollback posture exist
- next-package specificity:
  - explicit staged migration order exists
- restart-compressible now:
  - no as the first exact family

Why it does not win:

- it remains blocked by both shared-contract seams and env/schema ownership clarity
- it is execution-later by design

### 4. Repo bootstrap and extraction dependency family

- decisive receipt support:
  - `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-PLAN-2026-05-24.md`
  - `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
- blocked-work specificity:
  - strongest concrete extraction coupling inventory exists
- next-package specificity:
  - bootstrap package order is real, but still derivative of the seam, env, schema, and runtime chain
- restart-compressible now:
  - no as the first exact family

Why it does not win:

- it is the most downstream family in the current ladder
- it reflects the consequences of unresolved seams and ownership classes rather than their earliest controlling cause

## Exact Compression Decision

`compressed to one exact blocker family`

The exact winning family is:

- `shared-contract seam dependency family`

Why compression to one family is honest:

- the seam family is the clearest upstream blocker
- the other three families are still real, but they are later families rather than co-equal next families
- restart truth is clearer if the lane names the earliest exact family first instead of keeping four families artificially level

## Residual Ladder After Compression

The exact residual blocked-work ladder is now:

1. `shared-contract seam dependency family`

The following families remain later and dependent rather than current co-equal next blockers:

- `env/runtime ownership dependency family`
- `runtime cutover dependency family`
- `repo bootstrap and extraction dependency family`

## Exact Next Package

`Dependency Untangling shared-contract seam dependency family shaping pass 3`

Purpose:

- keep the lane root-bounded
- turn the seam family from a single exact blocker family into one operator-usable next-package chain
- freeze the seam-local blocked-work order and exact no-move-yet constraints without executing code movement or runtime cutover

Why this next package is honest:

- compression is complete, but the winning family still needs its own bounded operator lane
- the lane is not ready for hidden execution-by-stealth
- a seam-family shaping pass can now stay narrow without revisiting the full four-family ladder

## Marker Decision

Hold:

- `Dependency Untangling: 70% -> 70%`

Why:

- restart reality got narrower
- no live dependency class was cleared
- this is control-plane compression, not untangling execution

## What This Pass Proves

This pass proves:

- the four-family ladder no longer needs to stay artificially wide
- one exact blocker family is now strong enough to own the next lane
- restart can now resume `Dependency Untangling` from one upstream family rather than re-ranking four families from scratch

This pass does not prove:

- that the shared-contract seam family is resolved
- that env/runtime ownership is execution-ready
- that runtime cutover or repo extraction can begin now

## Exact Recommended Next Move

`Dependency Untangling shared-contract seam dependency family shaping pass 3`

## Rule

Compress the ladder to the earliest exact family, not the loudest downstream family.

## Pattern

shape the lane -> admit it into manifest-backed restart -> compress the blocker ladder -> isolate one upstream family -> only then shape the family-local next package

## Failure Mode

The lane keeps four blocker families open after one upstream family is already clearly governing the others, so restart stays wider and blurrier than the durable evidence requires.
