# ATLAS Ingest And Cleanup Guardrails

This document defines how ATLAS absorbs useful material while reducing machine clutter.

The operating rule is not "copy once, then delete." The operating rule is "migrate useful knowledge into the right canonical lane, keep lineage visible, and delete originals only when removal is verified safe."

## Core Rule

- Live implementation truth belongs in the repo that owns the code or active docs.
- ATLAS keeps cross-repo lineage, boundary summaries, and phase tracking instead of duplicating live implementation detail.
- Archive or recovered machine material should enter ATLAS manifest-first or by selective ingest, not by blind repo import.
- Original material is not a deletion candidate just because it was seen once.

Delete or replace an original only after one of these is true:

- the path is confirmed generated or vendor output that can be rebuilt
- the path is a dead shim or compatibility wrapper with a documented successor
- the retained ATLAS or repo-local record makes the original safely superseded

## Live Repo Boundaries

For active work, the source of truth should move toward the owning repo and away from duplicated stack docs.

Current example:

- `docs/architecture/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md` records the stack boundary only
- `repos/fawxzzy-fitness/docs/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md` is the implementation contract

That slice establishes the current pattern:

- repo-local contract holds live implementation truth
- ATLAS keeps a short lineage and pointer record
- ATLAS should not carry duplicate file inventories once the repo-local contract exists

## Archive And Recovery Ingest

Machine cleanup and archive recovery should classify material before adoption.

Current ingest posture:

| Item | Current posture | Guardrail |
| --- | --- | --- |
| `desktop` | mixed archive | keep as a collection-level manifest and split into subproject catalogs before any repo-ingest decision |
| `temp` | manifest-only provenance sample | retain manifest-only unless a specific fixture import is needed |
| `solar-flare` | unresolved placeholder | keep unresolved and continue searching approved roots; do not treat the placeholder folder as recovered project content |

Operational rules:

- Mixed bundles stay cataloged until their subprojects are separated.
- Unresolved placeholders stay on the hunt list instead of being promoted into fake repos.
- Manifest-only items may support provenance or fixture review without becoming source repos.
- ATLAS docs should avoid machine-specific absolute paths even when raw manifests capture local-only provenance.

## Verified Cleanup Only

Cleanup passes may remove only explicit junk or generated residue that has already been classified as safe to regenerate.

Current reclaim model:

- the generated-artifact reclaim pass removed about `28.0 GB`
- removed paths were report-listed generated trees such as `.vs`, `Binaries`, `Intermediate`, `Saved/Crashes`, `Saved/Temp`, and empty `DerivedDataCache`
- no repo roots or authored content were part of that pass

This is the approved cleanup posture:

- ingest or pointerize valuable material first
- keep mixed or unresolved material cataloged until understood
- delete only verified generated trash, dead shims, or safely superseded originals

## Source Snapshot

This guardrail summary reflects the stack state reviewed on `2026-04-11` from:

- `docs/architecture/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md`
- `data/exports/atlas-ingest/atlas-ingest-registry.csv`
- `data/exports/atlas-ingest/descendant-registry.csv`
- `tmp/cleanup-manifests/20260410-195055/reclaimed-space-summary.md`
