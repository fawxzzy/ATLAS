# Durable Context Externalization Continuity-Manifest Adoption Pass 1 - 2026-05-27

- Date: `2026-05-27`
- Lane: `Durable Context Externalization continuity-manifest adoption pass 1`
- Mode: `docs-only continuity adoption posture`
- Source surfaces:
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-CONTINUITY-MANIFEST-PASS-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-RETRIEVAL-SURFACE-INVENTORY-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-PROMPT-PACK-NORMALIZATION-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-MARKER-RATCHET-CHECKPOINT-2-2026-05-27.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/memory/README.md`
  - `docs/PLAYBOOK_NOTES.md`
- Control-plane checkpoint: `main@30274e9`

## Objective

Define the first adoption posture for continuity manifests so `manifest-backed` continuity means a real restart discipline, not a label applied before workers can actually reconstruct a lane from durable artifacts.

This pass does not:

- rewrite owner-repo docs
- create retrieval automation
- create fake manifest coverage for lanes that do not yet have it
- duplicate owner truth into ATLAS
- touch runtime, schema, env, or application code

## Root State

- branch: `main`
- HEAD: `30274e9`
- status: clean except intentional untracked `archive/`
- validation: green before adoption drafting at `critical=0 error=0 warning=310`

## Current Durable Baseline

Already durable before this pass:

- marker definition and rubric
- retrieval-surface taxonomy
- continuity-manifest contract
- prompt-pack normalization
- restart-guide manifest-first retrieval posture

What is still missing before the lane can claim broad operational maturity:

- an explicit adoption threshold for when a lane is honestly `manifest-backed`
- a first bounded set of lanes that should carry manifests before the posture is treated as normal
- a clear rule for how manifests relate to restart guides, receipt chains, and owner truth surfaces

## First Adoption Set

The first lanes that should carry continuity manifests are:

1. `Durable Context Externalization`
2. `Local Data Gateway`
3. `Discord OS Feedback Workflow Canonicalization`
4. `Discord OS Infrastructure Separation`

Why these first:

- they are cross-repo or cross-surface lanes
- they already depend on a receipt chain rather than one single file
- they already route through ATLAS doctrine plus owner-repo truth-owner surfaces
- restart quality for these lanes is most exposed to stale transcript recap and operator stitching

These are first-adoption targets, not proof that all four already have active manifests.

## Minimum Required Fields For An Adopted Manifest

An adopted continuity manifest must carry, at minimum:

### Manifest identity

- `manifest_id`
- `lane_id`
- `scope_class`
- `status`
- `created_at`
- `updated_at`

### Current durable checkpoint

- `current_checkpoint_receipt`
- `checkpoint_summary`
- `checkpoint_commit` when known

### Governing receipt chain

- ordered `governing_receipts`
- only the minimum current chain needed for reconstruction

### Owner truth routing

- `owner_truth_surfaces`
- references only, never copied owner content

### Verification or adoption routing

- `verification_adoption_surfaces`
- present when such proof surfaces materially affect restart or package choice

### Gate posture

- `blocked_or_gated_work`
- exact approval or proof requirement when one exists

### Next package ladder

- `next_package_ladder`
- at least one named next package with mode posture

### Marker posture

- relevant `marker_posture`
- only the markers that materially govern the lane

## When A Lane May Claim `Manifest-Backed` Continuity

A lane may claim `manifest-backed` continuity only when all of the following are true:

1. an ATLAS-root continuity manifest exists for that lane
2. the manifest status is `active`
3. the manifest points to the current decisive receipt, not a stale checkpoint
4. the manifest points to owner truth surfaces instead of copying them
5. the manifest points to verification or adoption surfaces when those are part of trustworthy restart
6. blocked classes, gated classes, and next package posture are current
7. a worker using the restart guide can reconstruct the lane by following the manifest chain without relying on chat recap as the primary substrate

If any of those conditions fail, the lane is still:

- receipt-backed
- partially externalized
- or operator-stitched

but not yet honestly `manifest-backed`.

## Relationship To Restart Guides And Receipt Chains

The relationship is now:

- restart guide
  - global resume order and control-plane doctrine
- continuity manifest
  - lane-specific retrieval map
- receipt chain
  - durable checkpoint and evidence spine
- owner truth surfaces
  - live repo-owned truth
- verification or adoption surfaces
  - repo-owned proof that current claims are real

The manifest does not replace the restart guide.

The manifest does not replace the receipt chain.

The manifest does not replace owner truth.

It compresses restart routing so workers do not have to reconstruct the same chain manually from transcript memory every time.

## Owner-Boundary Rule

Manifest adoption must preserve root posture:

- ATLAS owns continuity routing
- owner repos own implementation and workflow truth
- manifests may reference owner truth-owner surfaces
- manifests must not restate repo-local truth in full

If a manifest starts copying runtime truth, workflow rules, or mutable repo state into ATLAS, it has crossed the line from continuity substrate into duplicate truth store.

## Exact Gaps That Still Keep Continuity Partly Manual

Continuity remains partly manual after this pass because:

- no first-adoption lane yet has an active seeded manifest recorded in the receipt spine
- restart flows are manifest-first in doctrine, but not yet manifest-backed in lane coverage
- workers still need to stitch together the current receipt chain manually for major lanes
- verification or adoption surfaces are inventoried, but not yet consistently pulled into lane-specific manifest routing

This is deliberate.

This pass freezes adoption posture before seeding manifests so later receipts can distinguish:

- contract exists
- adoption posture exists
- seeded manifests exist
- restart is actually manifest-backed

## Current Honest Continuity Read

What is true now:

- manifest-first doctrine is durable
- restart surfaces already prefer manifests over transcript recap
- the system is ready for first-adoption seeding

What is not yet true:

- broad lane continuity is already manifest-backed
- restart is yet universal enough to remove operator stitching
- repo-owned verification/adoption surfaces are uniformly wired into lane continuity

## Exact Next Package

`Durable Context Externalization continuity-manifest seeding pass 1`

Why:

- the contract is frozen
- the adoption threshold is now frozen
- the next honest move is to seed one or more first-adoption manifests for current cross-repo lanes rather than merely refining doctrine again

## Rule

Manifest adoption must externalize continuity without creating a second truth map that competes with owner repos.

## Pattern

restart guide -> active continuity manifest -> governing receipt chain -> owner truth surfaces -> verification/adoption surfaces -> transcript nuance last

## Failure Mode

`Manifest-backed` becomes a label applied before restart flows actually depend on the manifest contract.
