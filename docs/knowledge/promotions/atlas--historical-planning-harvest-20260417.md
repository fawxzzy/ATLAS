---
schema_version: atlas.knowledge.promotion.v1
archive_id: atlas--historical-planning-harvest-20260417
promotion_status: promoted
indexing_profile: derived_only
retention_class: operational
created_at: 2026-04-17T16:15:00Z
updated_at: 2026-04-17T16:15:00Z
---

# Promotion: atlas--historical-planning-harvest-20260417

## Derived Summary

This harvest promotes the first durable planning truths from the new continuity lane instead of leaving them in packets, raw imports, or session residue. The promoted facts are:

- ATLAS root remains a coordination and reporting surface, not a second canonical store for child-repo truth.
- Playbook planning owner truth currently lives in `repos/fawxzzy-playbook/docs/PLAYBOOK_PRODUCT_ROADMAP.md` and `repos/fawxzzy-playbook/docs/roadmap/ROADMAP.json`, with supporting structure under `repos/fawxzzy-playbook/docs/roadmap/`.
- Historical import lanes remain trust-bounded: raw `verta-core` and `verta-core-clean` stay quarantined or metadata-only, while `verta-core-sanitized` is the only promotion-eligible path in the reviewed Verta set.
- Downloads packets stay local-only residue until their durable content is promoted into repo-owned exports, root memory, or knowledge artifacts.

## Source Lanes Harvested

- root planning doctrine:
  `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
  `docs/ops/ATLAS-CONTINUITY-LANE.md`
  `docs/ops/ATLAS-CONTINUITY-HARVEST-BACKLOG.md`
  `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`
- live Playbook owner planning:
  `repos/fawxzzy-playbook/docs/PLAYBOOK_PRODUCT_ROADMAP.md`
  `repos/fawxzzy-playbook/docs/roadmap/ROADMAP.json`
  `repos/fawxzzy-playbook/docs/roadmap/REPO_ROADMAP_SYSTEM.md`
  `repos/fawxzzy-playbook/docs/roadmap/IMPLEMENTATION_PLAN_NEXT_4_WEEKS.md`
- reviewed historical imports:
  `data/imports/knowledge/personal/verta-core/EVALUATION.json`
  `data/imports/knowledge/personal/verta-core-sanitized/EVALUATION.json`
  `docs/knowledge/reviews/verta-core.md`
  `docs/knowledge/reviews/verta-core-scrub-report.md`

## Promoted Facts

1. The packet assumption that Playbook roadmap files lived at the repo root was stale for the live tree. The durable owner paths are under `repos/fawxzzy-playbook/docs/roadmap/`, and the continuity manifest now records those live paths explicitly.
2. `repos/fawxzzy-playbook/docs/roadmap/IMPLEMENTATION_PLAN_NEXT_4_WEEKS.md` is an archived execution-window snapshot, not a live operator truth surface. Historical harvest should index it, but current answers should prefer `docs/PLAYBOOK_PRODUCT_ROADMAP.md` and `docs/roadmap/ROADMAP.json`.
3. The reviewed Verta lane is still useful as historical planning evidence, but only inside explicit trust posture. Raw `verta-core` remains quarantined, `verta-core-clean` remains blocked by secret-risk findings, and `verta-core-sanitized` is the only reviewed lane that can contribute promotion-safe derived knowledge today.
4. The first practical next tranche remains `fitness` repo-local adoption, while root historical harvest continues by extending manifest-backed review and promotion rather than by adding more root doctrine files.

## Indexed-Only Residue

These sources remain indexed-only or pending review after this harvest:

- `data/imports/knowledge/personal/verta-core*/**`
- `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/NEXT_MOVES_20260413.md`
- `data/imports/knowledge/personal/verta-core/extracted/Verta-Core/RUN_NEXT.md`
- `Downloads/FITNESS-PLAYBOOK-ADOPTION-PACKET.md`
- `Downloads/CODEX-PROMPT-FITNESS-PLAYBOOK-ADOPTION.md`
- `Downloads/ATLAS-HISTORICAL-PLANNING-HARVEST-PACKET.md`
- `Downloads/CODEX-PROMPT-ATLAS-HISTORICAL-PLANNING-HARVEST.md`

## Evidence References

- continuity manifest: `data/imports/knowledge/continuity/harvest-manifest.json`
- continuity handoff: `runtime/receipts/handoffs/playbook-convergence-historical-planning-harvest-20260417t161500z.handoff.json`
- root doctrine:
  `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
  `docs/ops/ATLAS-CONTINUITY-LANE.md`
  `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`
- Playbook owner planning:
  `repos/fawxzzy-playbook/docs/PLAYBOOK_PRODUCT_ROADMAP.md`
  `repos/fawxzzy-playbook/docs/roadmap/ROADMAP.json`
- reviewed Verta evidence:
  `docs/knowledge/reviews/verta-core.md`
  `docs/knowledge/reviews/verta-core-scrub-report.md`
  `data/imports/knowledge/personal/verta-core/EVALUATION.json`
  `data/imports/knowledge/personal/verta-core-sanitized/EVALUATION.json`
