# Commit And PR Flow

This document describes the ATLAS operator flow for turning a Codex handoff JSON file into commit text and PR text.

## Preconditions

Before running the helper scripts:

1. generate a handoff JSON file under `runtime/receipts/handoffs/`
2. validate the handoff against `ops/codex/schemas/change_handoff.schema.json`
3. review changed files in the target repo before any git mutation

The helper scripts read only the handoff JSON. They do not scrape transcript or UI text.

## Preferred Capture Flow

Use `ops/codex/run_scoped_task_with_handoff.ps1` to reserve the output file path and inject that path into the Codex command template.

The wrapper expects the Codex command template to include:

- `{HANDOFF_PATH}` or `{HANDOFF_ATLAS_PATH}`
- preferably `{SCHEMA_PATH}` or `{SCHEMA_ATLAS_PATH}`

The exact Codex flags depend on the installed Codex build. ATLAS keeps the output file path and schema path stable even if vendor flags change.

On Windows PowerShell, it is safest to build the command as an array first:

```powershell
$codexCommand = @(
  'codex',
  'exec',
  '--final-output-file',
  '{HANDOFF_ATLAS_PATH}',
  '--output-schema',
  '{SCHEMA_ATLAS_PATH}'
)

powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\run_scoped_task_with_handoff.ps1 `
  -TaskName atlas-handoff `
  -Workspace . `
  -CodexCommand $codexCommand `
  -PreviewOnly
```

Replace the flag names in that array with the ones supported by the local Codex build. The ATLAS contract stays the same.

## Preview A Handoff

Preview the structured contents of a handoff without mutating git:

```powershell
python .\ops\codex\validate_handoff.py --handoff-file .\tmp\scratch\handoff.synthetic.json --preview
```

Validate the schema definition itself:

```powershell
python .\ops\codex\validate_handoff.py --schema-file .\ops\codex\schemas\change_handoff.schema.json
```

Generate and validate a synthetic example:

```powershell
python .\ops\codex\validate_handoff.py --write-synthetic .\tmp\scratch\handoff.synthetic.json --preview
```

## Generate Commit Text

Preview the commit message that would be used:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_from_handoff.ps1 `
  -HandoffFile .\tmp\scratch\handoff.synthetic.json `
  -RepoPath . `
  -Mode preview
```

The script writes a commit message file beside the handoff by default.

Execute the commit only when ready:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_from_handoff.ps1 `
  -HandoffFile .\runtime\receipts\handoffs\<task>.handoff.json `
  -RepoPath . `
  -Mode commit
```

Optionally stage tracked and untracked changes in that repo first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_from_handoff.ps1 `
  -HandoffFile .\runtime\receipts\handoffs\<task>.handoff.json `
  -RepoPath . `
  -Mode commit `
  -StageAll
```

## Generate PR Text

Render a PR preview file from the handoff:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\prepare_pr_from_handoff.ps1 `
  -HandoffFile .\tmp\scratch\handoff.synthetic.json `
  -OutputPath .\tmp\previews\handoff.synthetic.pr.md
```

The rendered file includes:

- the PR title
- the PR body
- the source handoff path

## Approval And Protection Boundaries

Preview mode is the default because git mutation may still need approval outside ATLAS:

- some shells sandbox or block `.git` operations
- enterprise policy may require signed commits
- branch protection may block direct pushes
- PR creation usually still requires remote credentials and repo permissions

If `.git` is sandboxed or protected, the recommended operator flow is:

1. validate and preview the handoff
2. render the commit message file
3. render the PR preview file
4. run the actual `git commit`, push, and PR creation step in an approved shell or hosting UI

## Operational Notes

- keep handoff paths ATLAS-relative in commands and docs
- keep runtime artifacts under `runtime/receipts/handoffs/` or `tmp/previews/`
- do not copy generated commit or PR text into repo source files
- treat the handoff JSON as the source for commit and PR generation
