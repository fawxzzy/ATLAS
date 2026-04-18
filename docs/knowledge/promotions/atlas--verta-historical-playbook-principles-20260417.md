---
schema_version: atlas.knowledge.promotion.v1
archive_id: atlas--verta-historical-playbook-principles-20260417
promotion_status: promoted
indexing_profile: derived_only
retention_class: operational
created_at: 2026-04-17T18:20:00Z
updated_at: 2026-04-17T18:20:00Z
---

# Promotion: atlas--verta-historical-playbook-principles-20260417

## Source Record

- source id: `imports_verta_architecture_decision`
- source path: `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/docs/ARCHITECTURE_DECISION.md`
- title: `Verta Architecture Decision`
- source type: `imported_doc`
- provenance: reviewed derivative note authored in ATLAS from visible-untrusted Verta historical evidence
- trust posture: trusted derivative note; source evidence remains `visible_untrusted` and metadata-governed

## Derived Summary

This source carries forward the most useful Playbook and Verta principles for Atlas: deterministic-first behavior, fail-closed honesty, explicit provenance, complete verticals instead of partial capability, and portability through root-independent paths. Those principles are historically important because they explain why Atlas continuity favors explicit artifacts over transcript recall and why child repos stay owners of implementation truth.

## Key Claims

| Claim | Classification | Status | Current mapping |
| --- | --- | --- | --- |
| Deterministic-first behavior should outrank unsupported guesswork. | historical-intent | active | `docs/ops/ATLAS-CONTINUITY-LANE.md` |
| Provenance and explicit confidence are required for trustworthy operator answers. | historical-intent | active | `docs/ops/ATLAS-AWARENESS-API-RUNBOOK.md` |
| Atlas portability requires avoiding hardcoded roots and hidden coupling. | historical-intent | active | `stack.yaml` |
| Owner-repo implementation truth must stay in child repos rather than root. | owner-truth | active | `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md` |
| This source alone proves every later ATLAS governance rule. | unsupported | unclear | later ATLAS root doctrine makes those rules explicit |

## Topic Map

- Playbook principles into Atlas
- deterministic-first
- fail-closed
- provenance
- complete verticals
- portable paths

## Current Mappings

- root doctrine: `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
- continuity doctrine: `docs/ops/ATLAS-CONTINUITY-LANE.md`
- path policy: `stack.yaml`
- historical anchor: `docs/knowledge/promotions/atlas--historical-planning-harvest-20260417.md`

## Evidence References

- raw source: `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/docs/ARCHITECTURE_DECISION.md`
- archive review: `docs/knowledge/reviews/verta-core.md`
- sanitized archive evaluation: `data/imports/knowledge/personal/verta-core-sanitized/EVALUATION.json`
- trust gate: `docs/ops/VERTA-TRUST-GATE.md`

## Exclusions And Redactions

- The Verta archive remains untrusted and metadata-only at the archive level.
- This note retains only high-level doctrine, not raw architecture text or executable guidance.
- Any current owner-truth claim must still be backed by a live ATLAS or owner-repo surface.
