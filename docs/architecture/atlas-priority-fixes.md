# ATLAS Priority Fixes

Audit date: 2026-04-11

## Freeze Point

The stack policy is frozen at this boundary:

- live implementation truth stays in the owning repo
- ATLAS stays lineage- and boundary-oriented
- `data/exports/atlas-ingest/` stays local review evidence unless a specific export is deliberately promoted after it clears the stability and portability gate

The current ingest registry already matches that posture:

- `desktop` remains a mixed archive at the parent level, but its child catalogs now live under `docs/knowledge/catalogs/desktop/`
- `desktop/lrpython-linear-regression` now has a copy-first selective-ingest child archive at `data/imports/knowledge/personal/desktop-lrpython-linear-regression`
- `desktop/robocode` and `desktop/python-course-material` remain reference-first
- `temp` remains manifest-only provenance
- `solar-flare` remains unresolved

## Next Queue

1. Finish mobile-regression consolidation inside `repos/fawxzzy-fitness`.
   The extracted boundary is already real. The remaining decisions are downstream cleanup and whether `scripts/build-mobile-regression-boards.py` stays the long-term public wrapper or yields later to an explicit CLI cutover.
2. If desktop work continues, keep any LRPython follow-up scoped to the imported child archive and preserve the parent-original slice.
   Do not widen that work into repo ingest or whole-desktop cleanup.
3. Keep `desktop/robocode` and `desktop/python-course-material` reference-first until one exact extraction need appears.
4. Leave the export lane unchanged until one exact CSV or JSON file earns promotion under the current policy.

## Deferred On Purpose

- Do not broaden ATLAS stack work back into repo-local implementation cleanup outside the named mobile-regression slice.
- Do not promote the whole `desktop` bundle as one recovered project.
- Do not collapse the tracked `desktop` child catalogs back into a single ingest decision.
- Do not delete desktop originals just because a child-level decision exists.
- Do not blanket-unignore `data/**` just to track review exports.
