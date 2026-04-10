# Commit And PR Flow

This document describes the ATLAS operator flow for turning a Codex handoff JSON file into commit text and PR text.

It also covers the stack-root helper for committing dirty registered repos independently from the ATLAS root.

## Preconditions

Before running the helper scripts:

1. generate a handoff JSON file under `runtime/receipts/handoffs/`
2. validate the handoff against `ops/codex/schemas/change_handoff.schema.json`
3. review changed files in the target repo before any git mutation

The helper scripts read only the handoff JSON. They do not scrape transcript or UI text.

## Multi-Repo Commit From ATLAS Root

Script:

- `ops/codex/commit_stack_repos.ps1`
- `ops/codex/commit_stack_repos.cmd`

Purpose:

- read `stack.yaml` as the source of repo truth
- detect which registered repos are dirty
- print a clear summary before mutation
- commit each dirty child repo independently
- optionally commit the ATLAS root control repo separately after child repos with `-IncludeRoot` or `-RepoIds stack`

Rule:

- independent child repos must keep independent commit history even when orchestrated from the root control repo

Pattern:

- automate repo discovery and per-repo commit execution from the stack root, then optionally commit root metadata separately

Failure Mode:

- treating the control repo as if it can absorb child repo file diffs leads to missing commits, confusing status, and false confidence

Operational notes:

- the root control repo stays separate from child repos by design
- legacy and unmanaged repos are skipped by default unless explicitly targeted
- ignored files remain ignored because staging happens inside each repo with normal git rules
- one repo failing does not stage or commit another repo by accident because each git command runs against one resolved repo root at a time

Dry-run the current stack:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 -DryRun
```

Commit only specific child repos:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 `
  -RepoIds mazer,fitness `
  -CommitMessage "chore: sync local updates"
```

Commit child repos and then evaluate the root control repo separately:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 `
  -IncludeRoot `
  -RepoIds mazer,fitness `
  -CommitMessage "chore: sync local updates" `
  -CommitMessagePrefix "[atlas] " `
  -CommitMessageSuffix " root-orchestrated"
```

Root commit vs child repo commits:

- child repo commits are created inside each child repo and contain that repo's actual file diffs
- the ATLAS root commit can only record ATLAS-root files such as docs, ops scripts, and stack metadata
- the root repo cannot absorb or preserve a child repo's internal file diffs for it

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

## Multi-Repo Commit Helper

Use the stack-level commit helper from the ATLAS root when you need to commit dirty child repos independently without opening each repo by hand.

The helper reads `stack.yaml`, detects registered repos, prints the dirty/clean summary first, and then commits each selected dirty repo in isolation. The ATLAS control repo is treated separately, is opt-in by default, and only commits stack-level files, not child repo internals.

Rule:

- independent child repos must keep independent commit history even when orchestrated from the root control repo

Pattern:

- automate repo discovery and per-repo commit execution from the stack root, then optionally commit root metadata separately

Failure Mode:

- treating the control repo as if it can absorb child repo file diffs leads to missing commits, confusing status, and false confidence

Primary command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 -DryRun
```

Target only specific repos:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 -RepoIds stack,mazer
```

Include the root control repo in the same orchestrated pass:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 -IncludeRoot -RepoIds mazer
```

Add a shared prefix or suffix to each repo commit message:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 `
  -RepoIds stack,fitness `
  -CommitMessagePrefix "[atlas]" `
  -CommitMessageSuffix "Codex stack helper"
```

Dry-run output shows:

- which repos were dirty
- which repos were selected
- which repos would be committed
- which repos were skipped by default policy

Real-run output shows the same summary first, then stages and commits each selected repo one at a time. The root `stack` repo is committed separately and only against stack-level paths such as `docs`, `ops`, `data`, `packages`, `stack.yaml`, `README-STACK.md`, and `AGENTS.md`.

Example real run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\codex\commit_stack_repos.ps1 -RepoIds mazer,stack
```

Example `.cmd` wrapper:

```powershell
.\ops\codex\commit_stack_repos.cmd -DryRun -RepoIds stack,playbook
```

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
