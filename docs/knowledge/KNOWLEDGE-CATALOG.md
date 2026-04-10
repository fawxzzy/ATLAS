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
| `normalization_allowed` | Whether metadata may be retained in the runtime catalog |
| `risk_summary` | Short list of active risk flags |
| `notes` | Short explanation of the decision |

## Current State

The intended machine-readable companion lane is:

- `runtime/cortex/catalog/knowledge/`

The intended raw import lane is:

- `data/imports/knowledge/`

## Catalog Records

<!-- KNOWLEDGE-CATALOG:BEGIN -->
| archive_id | source | privacy_flag | status | safe_for_indexing | normalization_allowed | risk_summary | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `personal--college-fullstack-ai-archive` | `personal` | `private` | `normalized` | `restricted` | `yes` | `personal_private_material, copyrighted_courseware_risk, executable_content` | `Treat the archive as private or partially private. No active credentials were found after human review, but keyword-only secret hits remain documented. Courseware copyright signals were detected; retain metadata only. Executable or script content exists and must remain non-executed.` |
<!-- KNOWLEDGE-CATALOG:END -->

## Review Discipline

When a new archive is reviewed:

1. preserve the raw import in `data/imports/knowledge/`
2. document the decision in this catalog
3. write normalized runtime catalog entries only for accepted metadata
4. keep copied notes high-level and non-sensitive
5. do not treat imported courseware as stack-owned source