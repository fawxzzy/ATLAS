# Durable Context Externalization Continuity-Manifest Refresh Discipline Pass 1 - 2026-05-27

- Date: `2026-05-27`
- Lane: `Durable Context Externalization continuity-manifest refresh-discipline pass 1`
- Mode: `docs-only continuity-manifest lifecycle and freshness discipline`
- Source surfaces:
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-CONTINUITY-MANIFEST-PASS-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-CONTINUITY-MANIFEST-ADOPTION-PASS-1-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-CONTINUITY-MANIFEST-SEEDING-PASS-1-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-MARKER-RATCHET-CHECKPOINT-3-2026-05-27.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/memory/README.md`
  - `docs/PLAYBOOK_NOTES.md`
- Control-plane checkpoint: `main@8f10dda`

## Objective

Define the first explicit refresh discipline for seeded continuity manifests so the stack does not overclaim resumability just because manifests exist.

This pass does not:

- rewrite owner-repo truth docs
- implement retrieval automation
- claim automatic continuity
- refresh every stale manifest immediately
- touch runtime, schema, env, or application code
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `8f10dda`
- status: clean except intentional untracked `archive/`
- validation: green before discipline drafting at `critical=0 error=0 warning=310`

## Seeded Set Recomputed

Current first-adoption seeded manifests:

1. `docs/memory/initiatives/continuity-manifest-durable-context-externalization.json`
2. `docs/memory/initiatives/continuity-manifest-local-data-gateway.json`
3. `docs/memory/initiatives/continuity-manifest-discord-os-feedback-workflow-canonicalization.json`
4. `docs/memory/initiatives/continuity-manifest-discord-os-infrastructure-separation.json`

These still form the correct first-adoption set.

What changed since seeding is not the set itself, but the freshness posture:

- some manifests still point at older decisive receipts
- some marker-posture fields now trail current marker surfaces
- some next-package ladders now trail the current receipt chain

That means manifest presence alone is no longer enough to justify trusting every seeded manifest equally.

## Current Adoption Posture Recomputed

The adoption pass already froze the rule that a lane may claim `manifest-backed` continuity only when an active ATLAS-root manifest points to:

- the current decisive receipt
- owner truth-owner surfaces
- relevant verification/adoption surfaces
- current blocked or gated work
- current next-package posture

This pass adds the missing time-and-change discipline:

- a manifest can be present without still being fresh enough to be trusted as the primary restart map
- restart flows must distinguish:
  - `manifest-backed`
  - `manifest-present only`
  - `receipt-backed / operator-stitched`

## Refresh Discipline

### A manifest is stale when

A continuity manifest is stale when any of the following are true:

1. a newer decisive receipt exists for the same lane than the manifest's `current_checkpoint_receipt`
2. the lane's current marker posture in `docs/atlas-book/02-lanes-and-markers.md` no longer matches the manifest's `marker_posture`
3. the manifest's `next_package_ladder` no longer matches the current best next package named by the decisive receipt chain
4. blocked or gated work changed materially but the manifest still reflects the older gate posture
5. an owner truth-owner surface moved or was replaced in the receipt chain and the manifest still points to the wrong surface

Staleness is about routing correctness, not file age alone.

### Events that require refresh

Refresh is required after any of the following events:

- a marker ratchet changes the lane percentage in a way that alters restart interpretation
- a new decisive receipt changes the current checkpoint
- a new proof or implementation receipt changes the next-package ladder
- blocked or gated work changes materially
- owner routing changes materially
- a continuity-manifest receipt changes what counts as honest `manifest-backed` continuity

### What counts as `manifest-backed`

A lane is `manifest-backed` only when:

- a continuity manifest exists
- the manifest status is `active`
- the manifest is fresh under the rules above
- restart can follow that manifest to the current decisive receipt and current owner truth surfaces without transcript-first reconstruction

### What counts as `manifest-present only`

A lane is `manifest-present only` when:

- a continuity manifest exists
- but one or more freshness conditions above is no longer true

In that state:

- the manifest may still be useful as a partial retrieval map
- but it must not be treated as the primary restart authority until refreshed

### What remains `receipt-backed / operator-stitched`

A lane remains `receipt-backed / operator-stitched` when:

- no manifest exists
- or the manifest is too partial to route restart safely
- or restart still depends mainly on manual receipt-chain stitching

## How Restart Flows Should Handle Stale Or Partial Manifests

Restart order now becomes:

1. continuity manifest when one exists
2. check whether it is fresh enough to trust
3. if fresh:
   - follow manifest -> decisive receipt -> owner truth -> verification surfaces
4. if stale or partial:
   - treat the manifest as a hint only
   - fall back to the latest decisive receipt chain and canonical marker surfaces
   - do not claim the lane is currently `manifest-backed`

Operationally:

- a stale manifest should trigger verification, not confidence
- a partial manifest should narrow search, not end it

## Honest Read On The Current Seeded Set

After recomputing the seeded set against current durable state:

- the seeded-set doctrine is still correct
- the canonical manifest location is still correct
- but some seeded manifests are now better described as `manifest-present only` until refreshed

Examples of why:

- `Local Data Gateway` has moved past the seeded manifest's marker posture and next-package ladder
- `Durable Context Externalization` has moved past the seeded manifest's marker posture and checkpoint
- `Discord OS Feedback Workflow Canonicalization` has moved past the seeded manifest's checkpoint and next package

This is not a failure of the manifest concept.

It is proof that refresh discipline is necessary if manifests are going to stay trustworthy restart substrates.

## Owner-Boundary Rule

Refresh discipline must remain coordination-only:

- ATLAS owns continuity routing and freshness rules
- owner repos remain truth owners
- refreshing a manifest means updating references and lane posture
- it does not mean copying more owner truth into ATLAS

## What This Pass Prevents

Without refresh discipline, the stack can drift into stale comfort artifacts:

- manifests exist
- workers feel like continuity is externalized
- but the manifest now points at the wrong checkpoint or wrong next package

This pass prevents that by making freshness part of the `manifest-backed` claim itself.

## Exact Next Package

`Durable Context Externalization continuity-manifest refresh pass 1`

Why:

- the seeded set now needs a bounded refresh against current decisive receipts
- the discipline is durable
- the next honest move is to refresh the stale first-adoption manifests rather than only describing freshness in theory

## Rule

Refresh discipline must prevent continuity manifests from becoming stale comfort artifacts.

## Pattern

seed manifest -> lane advances -> freshness check -> refresh when checkpoint, marker, gate, or next-package posture changes -> only then keep the lane `manifest-backed`

## Failure Mode

A manifest exists, but restart flows trust it after the lane has already moved past it.
