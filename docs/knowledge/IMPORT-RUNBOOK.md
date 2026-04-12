# Knowledge Archive Import Runbook

This runbook defines the ATLAS-owned intake lane for personal learning materials, course packs, and AI study archives.

## Scope

- import a zip or folder into `data/imports/knowledge/<source>/<slug>/`
- preserve the original zip in `raw/` when present
- extract into `extracted/` for inspection without execution
- evaluate privacy, secrets, copyright, and executable-content risk
- normalize accepted metadata into `runtime/cortex/catalog/knowledge/`
- refresh `docs/knowledge/KNOWLEDGE-CATALOG.md`

The pipeline is stack-owned and does not mutate `repos/`.

## No-Execute Guarantee

- import uses file copy and safe zip extraction only
- evaluation scans filenames and text content only
- normalization writes metadata only
- human cataloging writes docs only
- imported scripts, notebooks, installers, and binaries are never launched by this lane

## Required Inputs

- a zip file or folder staged under ATLAS, typically in `tmp/scratch/`
- a source label such as `personal`, `course`, `training`, or `manual`
- an optional slug override when the incoming name is not stable enough
- a privacy flag:
  - `private`
  - `mixed`
  - `shareable`

## Commands

Zip import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/knowledge/import_archive.ps1 `
  -InputPath tmp/scratch/college-fullstack-ai-archive.zip `
  -SourceName personal `
  -Slug college-fullstack-ai-archive `
  -PrivacyFlag private
```

Folder import:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/knowledge/import_archive.ps1 `
  -InputPath tmp/scratch/college-fullstack-ai-archive `
  -SourceName personal `
  -Slug college-fullstack-ai-archive `
  -PrivacyFlag private
```

Evaluate without executing archive contents:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ops/knowledge/evaluate_archive.ps1 `
  -SourceName personal `
  -Slug college-fullstack-ai-archive
```

Normalize accepted metadata:

```powershell
python ops/knowledge/normalize_archive.py `
  --source-name personal `
  --slug college-fullstack-ai-archive
```

Refresh the human-readable catalog:

```powershell
python ops/knowledge/catalog_archive.py
python ops/knowledge/validate_knowledge_catalog.py
```

Dry-run any stage by appending `-DryRun` on the PowerShell wrappers or `--dry-run` on the Python commands.

## Output Layout

Imported archive:

- `data/imports/knowledge/<source>/<slug>/IMPORT-MANIFEST.json`
- `data/imports/knowledge/<source>/<slug>/raw/<archive>.zip` for zip inputs
- `data/imports/knowledge/<source>/<slug>/extracted/**`
- `data/imports/knowledge/<source>/<slug>/EVALUATION.json` after evaluation

Normalized metadata:

- `runtime/cortex/catalog/knowledge/<source>--<slug>.json`

Human catalog:

- `docs/knowledge/KNOWLEDGE-CATALOG.md`

Mixed collection catalogs:

- `docs/knowledge/catalogs/<collection>/`

## Review Flow

1. import the archive into the stack-owned lane
2. evaluate `EVALUATION.json` without opening executables
3. complete `docs/knowledge/REVIEW-TEMPLATE.md`
4. normalize only if metadata retention is acceptable for the archive
5. refresh and validate the catalog
6. keep any downstream indexing decision aligned with `safe_for_indexing`

For mixed recovery bundles that are too broad to classify as one archive or repo:

1. keep the parent item at collection level
2. write tracked child catalogs under `docs/knowledge/catalogs/<collection>/`
3. keep paths collection-relative instead of copying machine-local absolute paths into durable docs
4. make ingest-or-reference decisions per child catalog instead of promoting the whole parent bundle

Current example:

- `docs/knowledge/catalogs/desktop/README.md`

## Validation

Run these after a real intake:

```powershell
python ops/knowledge/validate_knowledge_catalog.py
python ops/validation/validate_stack.py
```
