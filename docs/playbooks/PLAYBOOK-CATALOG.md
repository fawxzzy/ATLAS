# Playbook Catalog

This document is the human-readable index for external playbook packs evaluated by ATLAS.

## Catalog Fields

| Field | Meaning |
| --- | --- |
| `pack_id` | Stable local identifier |
| `source` | Where the pack came from |
| `status` | `imported`, `evaluated`, `normalized`, `adopted_partially`, or `rejected` |
| `vendor_specificity` | `low`, `medium`, or `high` |
| `safety` | `allowed_for_review`, `restricted`, or `rejected` |
| `adoption_surface` | What ATLAS may reuse, if anything |
| `notes` | Short explanation of the decision |

## Current State

The intended machine-readable companion lane is:

- `runtime/cortex/catalog/playbooks/`

The intended raw import lane is:

- `data/imports/playbooks/`

## Catalog Records

<!-- PLAYBOOK-CATALOG:BEGIN -->
| pack_id | source | status | vendor_specificity | safety | adoption_surface | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `demo--synthetic-pack` | `demo` | `normalized` | `low` | `allowed_for_review` | `documentation and metadata` | `Pack can be reviewed without execution under the import/evaluate/normalize flow.` |
<!-- PLAYBOOK-CATALOG:END -->

## Review Discipline

When a new pack is reviewed:

1. preserve the raw import in `data/imports/playbooks/`
2. document the decision in this catalog
3. write normalized runtime catalog entries only for packs that survive evaluation
4. keep adopted concepts ATLAS-owned and vendor-neutral

## Example Entry Template

| pack_id | source | status | vendor_specificity | safety | adoption_surface | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `example-pack` | `manual import` | `evaluated` | `medium` | `allowed_for_review` | `review checklist only` | `Prompt templates were reusable; installer logic was rejected.` |
