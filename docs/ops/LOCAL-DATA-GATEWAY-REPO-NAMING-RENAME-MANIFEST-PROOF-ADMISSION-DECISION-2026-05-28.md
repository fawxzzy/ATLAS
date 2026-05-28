# Local Data Gateway Repo Naming Rename-Manifest Proof-Admission Decision - 2026-05-28

- Date: `2026-05-28`
- Owner: ATLAS root
- Mode: `docs-only proof-admission decision`
- Scope: `repo naming rename-manifest proof posture inside Local Data Gateway`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-RENAME-MANIFEST-CONTRACT-CHECKPOINT-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-EXPANSION-PASS-2-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-PROOF-PASS-1-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-9-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-SEND-AUTHORIZATION-PREREQUISITES-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-STREAM-BLOCKER-DISPOSITION-RATCHET-2026-05-28.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@b09b4a3`

## Objective

Decide whether the already-durable repo naming rename-manifest contract is now strong enough to admit one bounded proof class inside the Local Data Gateway lane without promoting repo naming workflows all the way to `adoptable now`.

This decision does not:

- modify `_stack`
- imply send-capable behavior
- authorize repo rename execution
- authorize remote or GitHub-side rename assumptions
- reopen the `fawxzzy-fitness` exception
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `b09b4a3`
- status: clean except intentional untracked `archive/`
- validation: green before drafting at `critical=0 error=0 warning=310`

## Current Local Data Gateway Workflow Classes Recomputed

### `adoptable now`

- Supabase export / approval-prep packet workflows
- Vercel dependency / deletion decision workflows
- DiscordOS trust-boundary / provenance proof workflows

### `adoptable later`

- Discord feedback evidence and parity packet families
- retained-surface destructive disposal packet families

### `out of scope`

- docs-native marker, doctrine, and ATLAS Book reconciliation receipts
- retained-surface registry-hygiene and similar direct truth-correction receipts

### repo naming family before this decision

Before this pass, Atlas-owned repo naming execution-readiness, approval, and proof / reconciliation packets still sat only at:

- `adoptable later`

because the family had local-only bounded value, but no family-specific packet contract strong enough to admit a narrower proof posture.

## Decision Question

The exact question is no longer whether repo naming is already `adoptable now`.

The exact question is whether the new rename-manifest contract is strong enough to admit one bounded middle class:

- `proof-admitted later`

Meaning:

- the family is still below operational no-send adoption
- but the contract is now strong enough that a bounded Local Data Gateway proof packet class can be judged honestly later without inventing new contract shape

## Proof-Admission Standard

For a family to enter `proof-admitted later`, all of the following must already be true:

1. the family has a durable packet or manifest contract for the bounded proof object
2. that contract is still strictly local-only and no-send
3. the contract can represent both successful and blocked execution truth without overclaiming operational adoption
4. the family still does not require hidden target selection, hidden transport, or hidden execution logic
5. the family remains clearly below `adoptable now`

If any of those fail, the family stays only `adoptable later`.

## Decision

Yes.

Atlas-owned repo naming now enters a narrower middle class:

- `proof-admitted later`

Equivalent bounded reading:

- `contract-complete but execution-blocked`

## Why This Middle-Class Admission Is Honest

The durable rename-manifest contract now freezes exactly the family-specific shape that was previously missing:

- rename candidate identity
- rewrite-surface inventory
- rollback order
- no-send attestation
- proof / reconciliation expectations

That contract is strong enough to admit one bounded proof class because it can now express:

- a local-only rename-manifest packet
- a blocked-before-rename outcome
- an executed-local-rename outcome
- explicit no-send and no-remote assumptions
- exact stale-reference and reconciliation boundaries

The contract therefore supports one bounded proof question:

- can the current no-send chain package repo naming truth honestly as a local proof artifact family

That is a proof-admission question.

It is not yet an adoption question.

## Why Repo Naming Still Does Not Reach `adoptable now`

Repo naming remains below `adoptable now` because the family still fails the stronger adoption test:

- the family still depends on execution-specific rewrite sequencing and reconciliation interpretation
- the useful workflow outcome is still tied to rename-lane execution state, not only stable packet production
- the active `stream` candidate is still execution-blocked by durable owner-side worktree blockers
- no proof yet exists that the current generic `validate -> emit -> review -> proof` chain can represent this family without gateway-specific rename logic

So the honest maturity is:

- above plain `adoptable later`
- below `adoptable now`

## Exact Admitted Bounded Proof Class

The admitted bounded proof class is:

- local-only rename-manifest proof packets for Atlas-owned repo naming candidates

This admitted proof class may cover:

- candidate identity capture
- rewrite-surface inventory capture
- rollback-order capture
- no-send attestation capture
- proof/reconciliation expectation capture
- blocked-execution proof packaging where blocked state is the honest outcome

This admitted proof class may not imply:

- rename execution approval
- automatic wrapper admission
- remote or GitHub rename semantics
- family-wide operational adoption
- send-capable helper behavior

## Relation To The Current Naming Lane

The current naming lane posture strengthens this decision rather than weakening it.

Why:

- the lane now has an explicit blocked-state interpretation
- the `stream` packet is durably blocked for known owner-side reasons
- the rename-manifest contract explicitly allows blocked execution to remain a valid proof outcome

That means the proof-admitted class does not need to pretend execution succeeded.

It can package blocked truth honestly.

## What This Pass Proves

This pass proves:

- repo naming no longer sits only in the undifferentiated `adoptable later` bucket
- the rename-manifest contract is now strong enough to admit one bounded no-send proof class
- blocked execution does not disqualify the family from proof admission when blocked truth is part of the contract

## What This Pass Does Not Prove

This pass does not prove:

- repo naming is now `adoptable now`
- `_stack` should implement repo naming packet logic
- the generic wrapper is already ready for this family
- any rename packet should be automated
- any marker move for `Local Data Gateway`

## Workflow Posture After This Decision

Updated Local Data Gateway posture for repo naming:

- `proof-admitted later`
- `contract-complete but execution-blocked`

That is the smallest honest refinement.

## Exact Next Package

`Local Data Gateway repo naming bounded proof-shape review`

Why:

- the contract is now strong enough for proof-admission
- the next honest question is whether one bounded proof packet shape can be reviewed against the current local-only chain without introducing gateway-specific rename behavior
- that still stays below implementation and below adopt-now graduation

## Rule

Proof-admission decisions must narrow workflow maturity honestly without silently graduating execution-blocked lanes into adopt-now.

## Pattern

family stays adoptable-later -> freeze family-specific manifest contract -> admit bounded proof class -> test proof-shape honesty -> only then reconsider broader adoption

## Failure Mode

A contract-complete workflow gets over-read as operationally adopted just because the manifest slice is well defined.
