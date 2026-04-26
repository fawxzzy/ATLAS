---
schema_version: atlas.knowledge.promotion.v1
archive_id: personal--unified-blueprint-curated-engine-atlas-fitness-playbook
promotion_status: promoted
indexing_profile: derived_only
retention_class: operational
created_at: 2026-04-26T06:42:50.319971Z
updated_at: 2026-04-26T06:43:05Z
---

# Promotion: personal--unified-blueprint-curated-engine-atlas-fitness-playbook

## Source Record

- title: `Unified Blueprint and Curated Engine for Atlas, Fitness, and Playbook`
- source type: `local_research_pdf`
- provenance: private strategy PDF imported into the ATLAS knowledge lane from a staged local copy
- trust posture: reviewed derivative note; the PDF is a planning and architecture input, not owner-repo truth

## Derived Summary

This PDF is worth retaining as continuation guidance because it makes one strong, source-aligned recommendation: do not rebuild the Atlas, Fitness, and Playbook interaction model from scratch. Instead, extract the best app-local contracts that already exist in Fitness into a shared stack contract layer, then land the curated workout engine behind those contracts. The durable value is the sequencing rule and system shape, not the point-in-time repo audit details.

The recommended sequence is consistent with current root doctrine: finish the current Fitness UI and UX pass, capture a screen delta ledger while the decisions are fresh, extract reusable screen, feature, token, and event contracts, then build the personalization and curated-engine layer on top of those contracts. The document also argues for a clear split between slow-changing shared config and live user state, with contract-first interfaces, event publishing, and a small blast-radius MVP before any ecosystem-wide rollout.

The engine guidance should be treated as cautious product strategy rather than scientific certainty. The retainable rule is to use cycle and diet inputs only as explicit opt-in modifiers, keep them low-confidence until user-specific evidence accumulates, and prefer reversible, explainable heuristics over opaque intelligence claims. Cross-app sharing should stay normalized and purpose-limited, with Atlas consuming only the context it needs rather than raw sensitive symptom detail.

## Accepted Guidance

- extract shared contracts before shared implementation
- treat Fitness as the first leverage point because it already contains the richest screen, state, feature, and theme scaffolding
- keep the curated engine behind a bounded MVP and feature flags before widening to other apps
- separate slow-changing config from fast-changing user personalization state
- keep cycle and diet support opt-in, minimal, and consent-bounded
- prefer adapter-based rollout across repos instead of forcing an early monorepo rewrite

## Current Mapping

- current root roadmap already carries the same contract-before-implementation rule in `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
- current root queue still keeps ML and broader shared-data work behind earlier contract, telemetry, and owner-truth gates in `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
- this promotion is therefore a continuity and planning input, not a live-status override
- the next implementation slices implied by this PDF belong primarily in `repos/fawxzzy-fitness`, with root retaining only the derivative summary and intake metadata

## Continuation Targets

- use the Fitness repo as the first extraction lane for `UIScreenMap`, `FeatureConfig`, shared tokens, and event-envelope contracts
- preserve a repo-local screen delta ledger while the current UI pass is still active
- keep Atlas focused on shared schemas, registry, and context projection rather than becoming the first personalization runtime by default
- use Playbook and Mazer-style validation surfaces to check contract completeness and drift once shared artifacts exist
- defer broader cross-app rollout until the Fitness-first contract surfaces are stable and verifiable

## Topic Map

- source: `personal`
- privacy flag: `private`
- safe_for_indexing: `restricted`
- planning theme: `fitness-first contract extraction`
- architecture theme: `shared contracts plus bounded personalization`
- sensitive domains: `cycle tracking`, `diet signals`, `health-adjacent personalization`
- representative paths: `unified-blueprint-curated-engine-atlas-fitness-playbook.pdf`

## Evidence References

- manifest: `data/imports/knowledge/personal/unified-blueprint-curated-engine-atlas-fitness-playbook/IMPORT-MANIFEST.json`
- evaluation: `data/imports/knowledge/personal/unified-blueprint-curated-engine-atlas-fitness-playbook/EVALUATION.json`
- import lane: `data/imports/knowledge/personal/unified-blueprint-curated-engine-atlas-fitness-playbook`
- extracted tree: `data/imports/knowledge/personal/unified-blueprint-curated-engine-atlas-fitness-playbook/extracted`
- extracted snapshot digest: `sha256:fd2c9c46879d029011235d05f983f222f294b22b751249de3ab77f091e7ee219`
- raw tree: `data/imports/knowledge/personal/unified-blueprint-curated-engine-atlas-fitness-playbook/raw`
- related stack doctrine: `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
- related stack doctrine: `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`

## Exclusions And Redactions

- This note does not promote the raw PDF text, research excerpts, or linked article content.
- This note does not treat the PDF's repo audit as canonical live posture for Atlas, Fitness, or Playbook.
- Health-adjacent implementation details still require repo-local product, privacy, and legal review before adoption.
- Sensitive user-context handling should remain normalized, minimal, and explicit-consent only.
