# Knowledge Promotion Runbook

This runbook defines the explicit promotion step for ATLAS knowledge archives after import and evaluation are complete.

## Purpose

- create durable promoted knowledge under `docs/knowledge/promotions/`
- keep raw evidence in `data/imports/knowledge/`
- keep runtime catalog entries rebuildable from manifest + evaluation + optional promotion docs
- record pipeline receipts in `runtime/receipts/knowledge/`

Promotion is optional. Do not create a promotion doc unless a human intends to retain derived knowledge beyond metadata-only handling.

## Promotion Preconditions

- `IMPORT-MANIFEST.json` exists
- `EVALUATION.json` exists
- `promotion_allowed = true`
- no-execute posture remains in force

Archives with `credentials_secrets_risk = true` must remain quarantined and cannot be promoted.

## Commands

Create or refresh a promotion doc:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/knowledge/promote_archive.ps1 `
  -SourceName personal `
  -Slug example-archive `
  -PromotionStatus draft `
  -IndexingProfile derived_only
```

Or call Python directly:

```powershell
python ops/knowledge/promote_archive.py `
  --source-name personal `
  --slug example-archive `
  --promotion-status draft `
  --indexing-profile derived_only
```

Normalize after promotion:

```powershell
python ops/knowledge/normalize_archive.py `
  --source-name personal `
  --slug example-archive
```

Refresh the human-readable catalog and validate:

```powershell
python ops/knowledge/catalog_archive.py
python ops/knowledge/validate_knowledge_catalog.py
```

## Required Front Matter

Each promotion doc must include:

- `schema_version: atlas.knowledge.promotion.v1`
- `archive_id`
- `promotion_status`
- `indexing_profile`
- `retention_class`
- `created_at`
- `updated_at`

## Required Sections

Each promotion doc must contain:

- `## Derived Summary`
- `## Topic Map`
- `## Evidence References`
- `## Exclusions And Redactions`

## Output Contract

Promotion docs live at:

- `docs/knowledge/promotions/<archive_id>.md`

Receipts live at:

- `runtime/receipts/knowledge/<archive_id>/`

Runtime catalog entries continue to live at:

- `runtime/cortex/catalog/knowledge/<archive_id>.json`

## Discipline

1. Keep the promoted summary high-level and provenance-aware.
2. Do not copy raw private notes, courseware, or secrets into the promotion doc.
3. Use `derived_only` when only the promoted summary and topic map should be indexable.
4. Use `full_text` only for confirmed shareable content.
5. If a promotion doc is removed, rerun normalization and catalog refresh so the runtime lane falls back to `not_promoted`.
