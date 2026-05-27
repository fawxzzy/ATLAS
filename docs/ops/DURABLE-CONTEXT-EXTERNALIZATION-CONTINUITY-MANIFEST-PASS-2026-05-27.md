# Durable Context Externalization Continuity-Manifest Pass - 2026-05-27

- Date: `2026-05-27`
- Lane: `Durable Context Externalization continuity-manifest pass`
- Mode: `docs-only continuity-manifest contract freeze`
- Source surfaces:
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-RETRIEVAL-SURFACE-INVENTORY-2026-05-27.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/memory/README.md`
- Control-plane checkpoint: `main@d607460`

## Objective

Define the first canonical continuity-manifest contract for resumable operator state and retrieval-first continuity without turning ATLAS into a duplicate truth store.

This pass does not:

- duplicate owner-repo runtime truth into ATLAS
- create retrieval automation
- create repo-local manifests inside owner repos
- inflate chat memory into a durable authority
- change runtime, schema, env, or application code

## Root State

- branch: `main`
- HEAD: `d607460`
- status: clean except intentional untracked `archive/`
- validation: green before contract drafting at `critical=0 error=0 warning=310`

## Why A Continuity Manifest Exists

ATLAS already has:

- a marker table
- a receipt spine
- a restart guide
- a system map
- durable memory slots

What is still missing is one reusable manifest shape that says, for a major lane:

- what lane is active
- what durable checkpoint currently governs it
- which receipts matter most
- which owner-repo surfaces carry the live truth
- which verification or adoption surfaces matter
- which work is blocked or approval-gated
- what the next package ladder is
- what the current marker posture is

The continuity manifest exists to externalize that resumable state as a retrieval map, not as a second source of truth.

## Canonical Continuity-Manifest Contract

### Purpose

A continuity manifest is a compact ATLAS-root artifact that points a worker to the minimum durable surfaces needed to reconstruct the current state of a lane or workflow chain without trusting prior chat continuity.

### Required Fields

#### 1. Manifest Identity

- `manifest_id`
- `lane_id`
- `scope_class`
  - `stack-root`
  - `cross-repo`
  - `owner-repo-reference`
- `created_at`
- `updated_at`
- `status`
  - `active`
  - `superseded`
  - `archived`

#### 2. Current Durable Checkpoint

- `current_checkpoint_receipt`
- `checkpoint_commit` when known
- `checkpoint_summary`

#### 3. Governing Receipts

- ordered list of the receipt chain that currently governs restart and interpretation

The list should prefer:

- the current decisive receipt
- the immediately relevant predecessor receipts
- only the minimum chain needed for reconstruction

#### 4. Owner-Repo Truth Surfaces

- ordered references to the repo-owned surfaces that define live truth for this lane

These should be references only, not copied content.

#### 5. Verification / Adoption Surfaces

- references to repo-owned verify, proof, adoption, or readiness surfaces that matter when deciding whether a claim is current or merely planned

#### 6. Blocked / Gated Work

- current blocked classes
- current approval-gated classes
- exact approval phrase or requirement when one exists

#### 7. Next Package Ladder

- `next_best_package`
- `next_best_package_mode`
  - `docs-only`
  - `approval-gated`
  - `open-execution`
- optional short ordered follow-on ladder if more than one next step matters

#### 8. Marker Posture

- relevant marker lines only
- current percentages only where they materially govern the lane

### Optional Fields

- `owner_surface_note`
- `restart_risks`
- `known_transcript_residue_risk`
- `supersedes_manifest_id`

## Manifest Boundaries

The continuity manifest may contain:

- references
- lane posture
- receipt ordering
- owner routing
- gate posture
- next-step posture

The continuity manifest must not contain:

- copied owner-repo implementation truth
- copied schema or runtime docs
- copied full receipt bodies
- copied raw transcript narrative
- copied mutable child-repo state as if root owns it

## Manifest Lifecycle

### When Created

Create a continuity manifest when:

- a major lane becomes governed enough that workers repeatedly need the same retrieval chain
- a lane has enough receipts and owner-boundary complexity that chat recap is becoming a continuity risk
- restart quality is suffering because the governing state is distributed across multiple surfaces

### When Refreshed

Refresh a continuity manifest when:

- the governing receipt changes
- the active lane changes
- owner routing changes
- blocked/gated posture changes
- the next package ladder changes materially
- marker posture changes in a way that alters restart interpretation

### When Superseded

Supersede rather than silently rewrite when:

- the lane’s governing checkpoint changes materially
- ownership posture changes materially
- the restart chain changes enough that the old manifest would now misroute work

### How Restart Flows Consume It

Restart order should become:

1. continuity manifest when one exists for the lane
2. current book chapter
3. receipt chain named by the manifest
4. owner-repo truth surfaces named by the manifest
5. verification/adoption surfaces named by the manifest
6. chat history only for unpromoted nuance

## Retrieval-First Doctrine Tightening

Continuity-manifest retrieval should be preferred before trusting chat continuity because it:

- compresses the retrieval chain without copying truth
- lowers the chance of stale receipt selection
- lowers the chance of wrong-repo or wrong-lane restart
- keeps owner boundaries explicit

## Suggested Manifest Template Shape

```yaml
manifest_id: atlas.continuity.<lane>.<date>
lane_id: <lane-name>
scope_class: stack-root | cross-repo | owner-repo-reference
status: active | superseded | archived
created_at: <iso-timestamp>
updated_at: <iso-timestamp>
current_checkpoint_receipt: <atlas-receipt-path>
checkpoint_commit: <sha-or-null>
checkpoint_summary: <one-paragraph-summary>
governing_receipts:
  - <atlas-receipt-path>
owner_truth_surfaces:
  - <repo-owned-doc-path>
verification_adoption_surfaces:
  - <repo-owned-proof-or-adoption-path>
blocked_or_gated_work:
  - class: <blocked-class>
    requirement: <approval-or-proof-requirement>
next_package_ladder:
  - package: <next-package-name>
    mode: docs-only | approval-gated | open-execution
marker_posture:
  - marker: <marker-name>
    percent: <value>
```

This is a contract sketch only.

It is not an implementation claim and not yet a required generated file.

## Initial Manifest Targets

The first good candidates for continuity-manifest use are:

- `Discord OS Infrastructure Separation`
- `Discord OS Feedback Workflow Canonicalization`
- `Local Data Gateway`
- `Durable Context Externalization` itself

Why these first:

- they are cross-repo or cross-surface lanes
- they already have a significant receipt chain
- they already have enough owner-routing complexity that stale chat recap is a real risk

## Ownership Boundary Note

The continuity manifest is an ATLAS coordination artifact.

It references:

- owner-repo truth
- owner-repo verification/adoption surfaces
- ATLAS receipts
- ATLAS book chapters

It does not replace any of them.

## Exact Next Package

`Durable Context Externalization prompt-pack normalization`

Why:

- the marker is admitted
- the retrieval surface taxonomy is now explicit
- the continuity-manifest contract is now frozen
- the next smallest honest move is to normalize active prompt/continuation surfaces so they all prefer manifest-first retrieval where appropriate

## Rule

Continuity manifests must externalize resumable state without becoming duplicate truth stores.

## Pattern

lane restart need -> continuity manifest -> receipt chain -> owner truth surfaces -> verification surfaces -> chat nuance last

## Failure Mode

A continuity manifest becomes a parallel source of truth instead of a durable retrieval map.
