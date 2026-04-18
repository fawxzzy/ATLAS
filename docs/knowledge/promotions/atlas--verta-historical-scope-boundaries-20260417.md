---
schema_version: atlas.knowledge.promotion.v1
archive_id: atlas--verta-historical-scope-boundaries-20260417
promotion_status: promoted
indexing_profile: derived_only
retention_class: operational
created_at: 2026-04-17T18:20:00Z
updated_at: 2026-04-17T18:20:00Z
---

# Promotion: atlas--verta-historical-scope-boundaries-20260417

## Source Record

- source id: `imports_verta_architecture_summary`
- source path: `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/docs/ARCHITECTURE_SUMMARY.md`
- title: `Verta Architecture Summary`
- source type: `imported_doc`
- provenance: reviewed derivative note authored in ATLAS from visible-untrusted Verta historical evidence
- trust posture: trusted derivative note; source evidence remains `visible_untrusted` and metadata-governed

## Derived Summary

This source is the strongest short-form answer to what was Playbook-specific versus Atlas-wide. It keeps Playbook and Verta as narrow operating systems or engines, while Atlas is described as the future outer orchestrator. That boundary is historically useful because it shows that whole-stack orchestration was already separated from repo-local or subsystem-specific capability.

## Key Claims

| Claim | Classification | Status | Current mapping |
| --- | --- | --- | --- |
| Playbook and Verta were treated as separate systems rather than the whole Atlas stack. | historical-intent | active | `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md` |
| Atlas was the future outer orchestrator, not yet built in that source. | historical-intent | partial | current ATLAS root now acts as the coordination layer |
| Repo-local or subsystem-specific acceleration should stay narrow instead of becoming a broad generic assistant. | historical-intent | active | `docs/ops/ATLAS-CODEX-CONTEXT-RUNBOOK.md` |
| The source proves that all future Atlas orchestration behavior was already implemented. | unsupported | unclear | later root doctrine and runtime artifacts establish live behavior |

## Topic Map

- Playbook specific versus Atlas wide
- Atlas future orchestrator
- narrow subsystem boundaries
- whole Atlas stack
- scope separation

## Current Mappings

- root coordination rule: `AGENTS.md`
- convergence doctrine: `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
- historical harvest: `docs/knowledge/promotions/atlas--historical-planning-harvest-20260417.md`

## Evidence References

- raw source: `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/docs/ARCHITECTURE_SUMMARY.md`
- archive review: `docs/knowledge/reviews/verta-core.md`
- trust gate: `docs/ops/VERTA-TRUST-GATE.md`

## Exclusions And Redactions

- This note does not convert Verta scope claims into live ATLAS implementation truth by itself.
- Raw architecture text remains in the quarantined import lane.
- Scope mappings stay high-level and provenance-aware.
