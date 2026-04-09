# ATLAS Stack Operations

This document covers bootstrap, validation, export, and restore for the ATLAS root.

## Bootstrap

Script:

- `ops/bootstrap/bootstrap_atlas.ps1`

Purpose:

- create missing directories from `stack.yaml`
- create required stack doc and ops lanes
- remain idempotent
- never overwrite secrets

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\bootstrap\bootstrap_atlas.ps1
```

## Validate

Scripts:

- `ops/validation/validate_stack.py`
- `ops/validation/validate_stack.ps1`

Purpose:

- read `stack.yaml` as the source of truth
- verify configured directories and repo paths exist
- check `AGENTS.md` and `.codex/config.toml` where expected
- detect common absolute-path leaks
- detect obvious mutable state left inside repos
- write markdown and json reports

Default report location:

- `runtime/receipts/validation/stack-validation.latest.md`
- `runtime/receipts/validation/stack-validation.latest.json`

Commands:

```powershell
python .\ops\validation\validate_stack.py
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\validation\validate_stack.ps1
```

Exit behavior:

- returns `2` when critical failures exist
- returns `0` when only errors or warnings exist

## Export

Script:

- `ops/backup/export_stack.ps1`

Purpose:

- create safe zip or snapshot exports
- export stack structure and selected repos
- document included and excluded material in an export manifest

Default inclusions:

- `stack.yaml`
- `README-STACK.md`
- `AGENTS.md`
- `docs/**`
- `ops/**`
- selected repos from `repo_registry`

Optional inclusions:

- `data/**` with `-IncludeData`
- `packages/**` with `-IncludePackages`

Default exclusions:

- `.git`
- `.venv`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`
- `.cache`
- `.turbo`
- `.parcel-cache`
- `node_modules`
- `.next`
- `dist`
- `coverage`
- `playwright-report`
- `test-results`
- `.vercel`
- `runtime/**`
- `tmp/**`
- `secrets/**`
- `.env`
- `.env.*`
- logs
- temp files
- sqlite and db files
- OS junk such as `Thumbs.db` and `.DS_Store`

Zip export examples:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\export_stack.ps1 -ZipPath .\packages\snapshots\atlas-structure.zip
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\export_stack.ps1 -ZipPath .\packages\snapshots\atlas-selected.zip -RepoIds fitness,playbook
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\export_stack.ps1 -ZipPath .\packages\snapshots\atlas-managed.zip -IncludeAllManagedRepos
```

Snapshot export example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\export_stack.ps1 -SnapshotPath .\packages\snapshots\atlas-snapshot -RepoIds stack,atlas
```

Every export contains:

- `EXPORT-MANIFEST.md`
- `EXPORT-MANIFEST.json`

Those manifest files state exactly what was included and what was excluded by default.

## Restore

Script:

- `ops/backup/restore_stack.ps1`

Purpose:

- restore from an export zip or snapshot directory
- skip `secrets/**`
- avoid overwriting existing files unless `-Overwrite` is set

Commands:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\restore_stack.ps1 -SourcePath .\packages\snapshots\atlas-structure.zip
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\restore_stack.ps1 -SourcePath .\packages\snapshots\atlas-snapshot -DestinationRoot C:\ATLAS-Restore
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\restore_stack.ps1 -SourcePath .\packages\snapshots\atlas-selected.zip -Overwrite
```

## Operational Notes

- bootstrap first when a new checkout is missing stack lanes
- validate after bootstrap and after any structural change
- export only from a validated stack when possible
- restore into a clean destination when testing recovery behavior
- secrets are intentionally outside default export and restore flows
