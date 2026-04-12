# ATLAS Ingest And Cleanup Guardrails

This document defines how ATLAS absorbs useful material while reducing machine clutter.

The operating rule is not "copy once, then delete." The operating rule is "migrate useful knowledge into the right canonical lane, keep lineage visible, and delete originals only when removal is verified safe."

## Freeze Point

The current freeze point is:

- live implementation truth stays in the repo that owns the active code or docs
- ATLAS stays lineage- and boundary-oriented instead of becoming a duplicate implementation repo
- `data/exports/atlas-ingest/` stays local review evidence unless one exact CSV or JSON export later clears the promotion gate

## Core Rule

- Live implementation truth belongs in the repo that owns the code or active docs.
- ATLAS keeps cross-repo lineage, boundary summaries, and phase tracking instead of duplicating live implementation detail.
- Archive or recovered machine material should enter ATLAS manifest-first or by selective ingest, not by blind repo import.
- Original material is not a deletion candidate just because it was seen once.

Delete or replace an original only after one of these is true:

- the path is confirmed generated or vendor output that can be rebuilt
- the path is a dead shim or compatibility wrapper with a documented successor
- the retained ATLAS or repo-local record makes the original safely superseded

## Two Canonical Lanes

ATLAS now operates with two explicit lanes:

- Live code and active docs move toward canonical ownership in the repo that owns the work.
- Recovered machine material stays catalog-first in ATLAS until it is classified and a selective ingest decision is justified.

The lanes share one cleanup rule:

- delete only after the retained repo-local or ATLAS record makes the original provably safe to remove

## Lane 1: Live Repo Boundaries

For active work, the source of truth should move toward the owning repo and away from duplicated stack docs.

Current example:

- `docs/architecture/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md` records the stack boundary only
- `repos/fawxzzy-fitness/docs/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md` is the implementation contract

That slice establishes the current pattern:

- repo-local contract holds live implementation truth
- ATLAS keeps a short lineage and pointer record
- ATLAS should not carry duplicate file inventories once the repo-local contract exists

## Lane 2: Archive And Recovery Ingest

Machine cleanup and archive recovery should classify material before adoption.

Current ingest posture:

| Item | Current posture | Guardrail |
| --- | --- | --- |
| `desktop` | mixed archive with tracked child catalogs | keep the parent as a collection-level manifest and make any later ingest-or-reference call per child catalog |
| `temp` | manifest-only provenance sample | retain manifest-only unless a specific fixture import is needed |
| `solar-flare` | unresolved placeholder | keep unresolved and continue searching approved roots; do not treat the placeholder folder as recovered project content |

Operational rules:

- Mixed bundles stay cataloged until their subprojects are separated.
- Unresolved placeholders stay on the hunt list instead of being promoted into fake repos.
- Manifest-only items may support provenance or fixture review without becoming source repos.
- ATLAS docs should avoid machine-specific absolute paths even when raw manifests capture local-only provenance.

Desktop split rule:

- Do not promote the `desktop` bundle wholesale.
- Keep the tracked child catalog under `docs/knowledge/catalogs/desktop/`.
- The current child lanes are `Robocode`, `LRPython / linear regression`, and general `Python/course material`.
- A copy-first selective ingest for `LRPython / linear regression` now exists at `data/imports/knowledge/personal/desktop-lrpython-linear-regression`.
- That imported child archive is limited to source, tests, CSV datasets, and `LRPython.pyproj`.
- `Robocode` and `Python/course material` remain reference-first until a narrower extraction need is justified.
- Keep originals in place until any child-level extraction or reclaim step is explicitly executed.

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

## Export Tracking Policy

Files under `data/exports/atlas-ingest/` are local review evidence by default and remain untracked unless explicitly promoted.

Current durability boundary:

- the root `.gitignore` ignores `data/**` by default
- copied CSV exports in `data/exports/atlas-ingest/` therefore stay local-only unless a workflow intentionally promotes a specific file
- the durable tracked truth for ingest posture remains the stack docs, while local exports support review, cataloging, and provenance checks

Promotion gate:

1. its schema is stable enough to survive review churn
2. its contents are normalized and not dependent on local absolute paths
3. it represents durable cross-session truth rather than a one-pass audit artifact
4. it does not duplicate a repo-local contract or stack doc that already owns the truth

Promotion should stay narrow and explicit:

- do not blanket-unignore `data/**`
- promote exact files one by one only after they cross the gate above
- if the durable truth already lives in a repo-local contract or stack doc, keep the export local-only

## Next Queue

Keep the queue narrow:

1. Finish mobile-regression consolidation inside `repos/fawxzzy-fitness`, where the extracted boundary is already established and the remaining decisions are downstream cleanup plus any later explicit CLI cutover.
2. If desktop work continues, keep LRPython follow-up scoped to the imported child archive and keep the other child lanes reference-first.
3. Leave the export lane alone until one exact CSV or JSON file actually earns promotion under the gate above.

## Source Snapshot

This guardrail summary reflects the stack state reviewed on `2026-04-11` from:

- `docs/architecture/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md`
- `docs/knowledge/catalogs/desktop/README.md`
- `docs/knowledge/reviews/desktop-lrpython-linear-regression.md`
- `data/exports/atlas-ingest/atlas-ingest-registry.csv`
- `data/exports/atlas-ingest/descendant-registry.csv`
- `tmp/cleanup-manifests/desktop-split/desktop-subprojects.md`
- `tmp/cleanup-manifests/20260410-195055/reclaimed-space-summary.md`
