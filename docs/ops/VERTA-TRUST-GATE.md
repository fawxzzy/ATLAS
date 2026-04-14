# Verta Trust Gate

Verta remains a standing trust gate, not a promotion lane.

## Guarded Surfaces

The root validation pass guards:

- `repos/Verta-Core`
- `repos/Verta-Core.zip`
- `runtime/cortex/catalog/knowledge/personal--verta-core.json`
- `runtime/cortex/catalog/knowledge/personal--verta-core-sanitized.json`

## Required Posture

- original Verta checkout and archive stay `trust_class = untrusted`
- original Verta surfaces stay `release_eligible = false`
- original Verta catalog stays `indexing_profile = metadata_only`
- sanitized candidate stays metadata-only and not promoted
- neither surface may gain a promotion doc without an explicit trust decision

## Validation Rules

`ops/validation/validate_stack.py` now enforces:

- explicit excluded-surface entries for the original checkout and archive
- `release_eligible = false` on both excluded surfaces
- metadata-only posture for the original and sanitized runtime catalogs
- a no-execute guarantee on both guarded catalogs
- secret-pattern scans on the live checkout and sanitized candidate trees

## Non-Goal

The trust gate does not promote Verta automatically. It only blocks silent drift back into trusted or releasable surfaces.
