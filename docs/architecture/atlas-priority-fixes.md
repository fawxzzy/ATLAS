# ATLAS Priority Fixes

Audit date: 2026-04-11

## Freeze Point

The stack policy is frozen at this boundary:

- live implementation truth stays in the owning repo
- ATLAS stays lineage- and boundary-oriented
- `data/exports/atlas-ingest/` stays local review evidence unless a specific export is deliberately promoted after it clears the stability and portability gate

The current ingest registry already matches that posture:

- `desktop` remains a mixed archive that must be split before any ingest decision
- `temp` remains manifest-only provenance
- `solar-flare` remains unresolved

## Next Queue

1. Finish mobile-regression consolidation inside `repos/fawxzzy-fitness`.
   The extracted boundary is already real. The remaining decisions are downstream cleanup and whether `scripts/build-mobile-regression-boards.py` stays the long-term public wrapper or yields later to an explicit CLI cutover.
2. Split the `desktop` ingest bundle into smaller subproject catalogs instead of promoting it wholesale.
   The minimum lanes already evidenced are `Robocode`, `LRPython / linear regression`, and general `Python/course material`.
3. Make the ingest-or-reference decision separately for each resulting desktop subproject catalog.
4. Leave the export lane unchanged until one exact CSV or JSON file earns promotion under the current policy.

## Deferred On Purpose

- Do not broaden ATLAS stack work back into repo-local implementation cleanup outside the named mobile-regression slice.
- Do not promote the whole `desktop` bundle as one recovered project.
- Do not blanket-unignore `data/**` just to track review exports.
