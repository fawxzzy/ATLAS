# Playbook Import Runbook

This runbook defines the first ATLAS-owned pipeline for third-party playbook packs.

## Scope

- import raw packs into `data/imports/playbooks/<source>/<slug>/`
- evaluate contents without executing vendor code
- normalize accepted metadata into `runtime/cortex/catalog/playbooks/`
- refresh `docs/playbooks/PLAYBOOK-CATALOG.md`

The pipeline is stack-owned and does not mutate `repos/`.

## No-Execute Guarantee

- no vendor hook, installer, daemon, or background process is started
- import uses file copy and safe zip extraction only
- evaluation uses filename and text scanning only
- normalization copies metadata, not vendor code
- raw vendor files stay under `data/imports/playbooks/`

## Required Inputs

- a folder or `.zip` pack
- a stack-relative or local source label such as `github`, `manual`, or `vendor-drop`
- an optional slug override when the incoming name is not stable enough

## Commands

Folder import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/playbooks/import_pack.ps1 `
  -InputPath tmp/scratch/playbook-demo `
  -SourceName demo `
  -Slug synthetic-pack
```

Zip import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/playbooks/import_pack.ps1 `
  -InputPath tmp/scratch/vendor-pack.zip `
  -SourceName vendor-drop `
  -Slug pack-name
```

Evaluate without executing vendor content:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/playbooks/evaluate_pack.ps1 `
  -SourceName demo `
  -Slug synthetic-pack
```

Normalize accepted metadata:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/playbooks/normalize_pack.ps1 `
  -SourceName demo `
  -Slug synthetic-pack
```

Refresh the catalog document:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/playbooks/catalog_pack.ps1
python ops/playbooks/validate_playbook_catalog.py
```

Dry-run any stage by appending `-DryRun` on the PowerShell wrapper.

## Output Layout

Imported pack:

- `data/imports/playbooks/<source>/<slug>/IMPORT-MANIFEST.json`
- `data/imports/playbooks/<source>/<slug>/raw/**`
- `data/imports/playbooks/<source>/<slug>/original/<archive>.zip` for zip inputs
- `data/imports/playbooks/<source>/<slug>/EVALUATION.json` after evaluation

Normalized metadata:

- `runtime/cortex/catalog/playbooks/<source>--<slug>.json`

Human catalog:

- `docs/playbooks/PLAYBOOK-CATALOG.md`

## Review Flow

1. import the raw pack
2. evaluate risk flags and provenance
3. complete `docs/playbooks/PACK-REVIEW-TEMPLATE.md`
4. normalize only if the pack is acceptable for metadata retention
5. refresh and validate the catalog
6. capture receipts by wrapping explicit commands through `ops/codex/run_scoped_task.ps1`

## Validation

Run these after a real or demo pass:

```powershell
python ops/validation/validate_event_contracts.py
python ops/playbooks/validate_playbook_catalog.py
python ops/validation/validate_stack.py
```
