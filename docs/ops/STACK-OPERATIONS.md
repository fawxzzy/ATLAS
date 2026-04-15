# ATLAS Stack Operations

This document covers bootstrap, validation, export, and restore for the ATLAS root.

See also:

- `docs/ops/ATLAS-SESSION-RUNBOOK.md`
- `docs/ops/ATLAS-ARTIFACT-DESCRIPTOR-RUNBOOK.md`
- `docs/ops/ATLAS-STATUS-RUNBOOK.md`
- `docs/ops/VERTA-TRUST-GATE.md`

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
- support a committed validation baseline for ratcheting
- classify inherited debt separately from new regressions
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

Write or refresh the committed baseline:

```powershell
python .\ops\validation\validate_stack.py --write-baseline
```

Run in ratchet mode so only new critical or error findings fail the command:

```powershell
python .\ops\validation\validate_stack.py --ratchet
```

Default baseline path:

- `ops/validation/stack-validation.baseline.json`

Debt tracking docs:

- `docs/audits/STACK-DEBT-LEDGER.md`
- `docs/backlog/STACK-DEBT-BURNDOWN.md`

Ratchet rule:

- inherited blocking findings stay visible by debt class
- only new blocking findings fail a healthy ratchet run
- governed-surface regressions are not debt and should not be normalized away

Knowledge-lane validation:

```powershell
python .\ops\knowledge\validate_knowledge_catalog.py
```

## Commit

Script:

- `ops/codex/commit_stack_repos.ps1`

Purpose:

- detect dirty registered repos from `stack.yaml`
- commit each selected dirty repo independently
- keep the root `stack` repo separate from child repo histories
- support `-DryRun`, `-IncludeRoot`, `-RepoIds`, `-CommitMessagePrefix`, and `-CommitMessageSuffix`

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 -DryRun
```

Use `-RepoIds mazer` to target only specific child repos. Add `-IncludeRoot` or target `stack` explicitly when the root control repo should be committed too.

Exit behavior:

- returns `2` when critical failures exist
- returns `0` when only errors or warnings exist

## Multi-Repo Commit

See the `Commit` section above for the current stack-aware helper and examples.

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
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\restore_stack.ps1 -SourcePath .\packages\snapshots\atlas-snapshot -DestinationRoot .\tmp\scratch\atlas-restore
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\backup\restore_stack.ps1 -SourcePath .\packages\snapshots\atlas-selected.zip -Overwrite
```

## Knowledge Query

Scripts:

- `ops/knowledge/build_query_bundle.py`
- `ops/knowledge/query_knowledge.py`

Purpose:

- build a deterministic query surface over promoted knowledge, runtime catalogs, and latest receipts
- keep query artifacts rebuildable under `runtime/cortex/query/knowledge/`
- let workers query promoted or metadata-safe knowledge without hydrating raw imports

Commands:

```powershell
python .\ops\knowledge\build_query_bundle.py
```

```powershell
python .\ops\knowledge\query_knowledge.py "verta core"
```

Operational rule:

- query artifacts are derived runtime state, not durable source truth

## Session Runner

Script:

- `ops/atlas/run_session.py`

Purpose:

- create one `atlas.session.v1` manifest
- build worker context
- emit worker assignment
- invoke `_stack` and record Lifeline receipt refs
- record supervisor pause/merge/resume refs when conflicts occur
- close the session with an explicit final status

Command:

```powershell
python .\ops\atlas\run_session.py --task-id atlas-session-readonly
```

## Descriptor Registry

Scripts:

- `ops/cortex/register_artifacts.py`
- `ops/cortex/render_status.py`

Purpose:

- register `atlas.artifact.descriptor.v1` files for governed runtime artifacts
- render a stable status view from descriptor metadata only

Commands:

```powershell
python .\ops\cortex\register_artifacts.py
```

```powershell
python .\ops\cortex\render_status.py
```

## Operational Notes

- bootstrap first when a new checkout is missing stack lanes
- validate after bootstrap and after any structural change
- export only from a validated stack when possible
- restore into a clean destination when testing recovery behavior
- secrets are intentionally outside default export and restore flows
