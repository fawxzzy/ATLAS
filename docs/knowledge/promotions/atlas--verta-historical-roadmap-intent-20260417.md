---
schema_version: atlas.knowledge.promotion.v1
archive_id: atlas--verta-historical-roadmap-intent-20260417
promotion_status: promoted
indexing_profile: derived_only
retention_class: operational
created_at: 2026-04-17T18:20:00Z
updated_at: 2026-04-17T18:20:00Z
---

# Promotion: atlas--verta-historical-roadmap-intent-20260417

## Source Record

- source id: `imports_verta_atlas_absorption_plan`
- source path: `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/docs/ATLAS_ABSORPTION_PLAN.md`
- title: `ATLAS Absorption Plan - Two-Track Export Strategy`
- source type: `imported_doc`
- provenance: reviewed derivative note authored in ATLAS from visible-untrusted Verta historical evidence
- trust posture: trusted derivative note; source evidence remains `visible_untrusted` and metadata-governed

## Derived Summary

The original Atlas roadmap shape in this historical Verta source was a two-track export strategy. The document framed an early repo-native transfer lane for a Work Kit and a slower, more embedded lane for Verta Core inside Atlas. That is useful as historical intent, but not as adopted schedule truth. The durable value today is the boundary logic: keep interfaces explicit, keep repo-native and embedded system scopes distinct, and let Atlas coordinate transfer contracts instead of flattening them into one truth store.

## Key Claims

| Claim | Classification | Status | Current mapping |
| --- | --- | --- | --- |
| The original Atlas roadmap shape used a two-track export strategy. | historical-intent | partial | `docs/knowledge/promotions/atlas--historical-planning-harvest-20260417.md` |
| Repo-native Work Kit and ATLAS-embedded Verta Core were treated as different transfer lanes. | historical-intent | partial | `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md` |
| Interface and ownership boundaries mattered more than merging everything into one system. | historical-intent | active | `docs/ops/ATLAS-CONTINUITY-LANE.md` |
| The specific month-3 and month-6-12 timeline became adopted ATLAS truth. | unsupported | unclear | no matching adopted root record was found |

## Topic Map

- original Atlas roadmap shape
- two-track export strategy
- Work Kit versus Verta Core
- transfer boundaries
- repo-native versus embedded scope

## Current Mappings

- newer stack doctrine: `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
- continuity anchor: `docs/knowledge/promotions/atlas--historical-planning-harvest-20260417.md`
- related historical PDF promotions:
  `docs/knowledge/promotions/personal--atlas-universal-interoperable-technology-stack.md`
  `docs/knowledge/promotions/personal--atlas-universal-extensible-ai-powered-os-ecosystem-inspired-by-linux-and-git.md`

## Evidence References

- raw source: `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/docs/ATLAS_ABSORPTION_PLAN.md`
- archive review: `docs/knowledge/reviews/verta-core.md`
- sanitized archive evaluation: `data/imports/knowledge/personal/verta-core-sanitized/EVALUATION.json`
- trust gate: `docs/ops/VERTA-TRUST-GATE.md`

## Exclusions And Redactions

- This note does not promote `personal--verta-core` or `personal--verta-core-sanitized` as trusted archive truth.
- Raw body text, schedules, and detailed implementation lists are not copied forward verbatim.
- Historical schedule claims remain historical intent unless a newer ATLAS-owned record adopts them.
