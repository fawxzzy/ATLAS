# Knowledge Catalog

This document is the human-readable index for imported knowledge archives reviewed by ATLAS.

## Catalog Fields

| Field | Meaning |
| --- | --- |
| `archive_id` | Stable local identifier |
| `source` | Where the archive came from |
| `privacy_flag` | `private`, `mixed`, or `shareable` |
| `status` | `imported`, `evaluated`, `normalized`, `indexed_metadata_only`, or `rejected` |
| `safe_for_indexing` | `pending_review`, `no`, `restricted`, or `yes` |
| `indexing_profile` | Downstream execution policy: `metadata_only`, `derived_only`, or `full_text` |
| `promotion_status` | `not_promoted`, `draft`, or `promoted` |
| `normalization_allowed` | Whether metadata may be retained in the runtime catalog |
| `risk_summary` | Short list of active risk flags |
| `notes` | Short explanation of the decision |

## Current State

The machine-readable companion lane is:

- `runtime/cortex/catalog/knowledge/`

The raw import lane is:

- `data/imports/knowledge/`

The promotion lane is:

- `docs/knowledge/promotions/`

The receipt lane is:

- `runtime/receipts/knowledge/`

## Catalog Records

<!-- KNOWLEDGE-CATALOG:BEGIN -->
| archive_id | source | privacy_flag | status | safe_for_indexing | indexing_profile | promotion_status | normalization_allowed | risk_summary | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal--atlas-stack-git-versioning-openai-integration-research` | `personal` | `private` | `normalized` | `restricted` | `derived_only` | `promoted` | `yes` | `personal_private_material` | `Treat the archive as private or partially private.` |
| `personal--atlas-storage-system-rule-based-compression-deduplication-graph` | `personal` | `private` | `normalized` | `restricted` | `derived_only` | `promoted` | `yes` | `personal_private_material` | `Treat the archive as private or partially private.` |
| `personal--atlas-universal-extensible-ai-powered-os-ecosystem-inspired-by-linux-and-git` | `personal` | `private` | `normalized` | `restricted` | `derived_only` | `promoted` | `yes` | `personal_private_material` | `Treat the archive as private or partially private.` |
| `personal--atlas-universal-interoperable-technology-stack` | `personal` | `private` | `normalized` | `restricted` | `derived_only` | `promoted` | `yes` | `personal_private_material` | `Treat the archive as private or partially private.` |
| `personal--college-fullstack-ai-archive` | `personal` | `private` | `normalized` | `restricted` | `metadata_only` | `not_promoted` | `yes` | `personal_private_material, copyrighted_courseware_risk, executable_content` | `Treat the archive as private or partially private. No active credentials were found after human review, but keyword-only secret hits remain documented. Courseware copyright signals were detected; retain metadata only. Executable or script content exists and must remain non-executed.` |
| `personal--desktop-lrpython-linear-regression` | `personal` | `private` | `normalized` | `restricted` | `metadata_only` | `not_promoted` | `yes` | `personal_private_material, executable_content` | `Treat the archive as private or partially private. Executable or script content exists and must remain non-executed.` |
| `personal--verta-core` | `personal` | `private` | `normalized` | `no` | `metadata_only` | `not_promoted` | `no` | `personal_private_material, credentials_secrets_risk, copyrighted_courseware_risk, executable_content` | `Treat the archive as private or partially private. Potential credentials or secret-bearing material were detected. Courseware copyright signals were detected; retain metadata only. Executable or script content exists and must remain non-executed.` |
<!-- KNOWLEDGE-CATALOG:END -->

## Review Discipline

When a new archive is reviewed:

1. preserve the raw import in `data/imports/knowledge/`
2. record the evaluation decision and indexing profile
3. create a promotion doc only when derived or promoted knowledge is intentional
4. write normalized runtime catalog entries from manifest, evaluation, and optional promotion docs
5. keep copied notes high-level and non-sensitive
6. do not treat imported courseware as stack-owned source