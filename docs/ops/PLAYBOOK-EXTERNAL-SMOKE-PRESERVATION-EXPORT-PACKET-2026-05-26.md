# Playbook External Smoke Preservation Export Packet - 2026-05-26

- Date: `2026-05-26`
- Lane: `Playbook external smoke preservation export packet`
- Mode: `artifact preservation only`
- Control-plane checkpoint: `main@9df0627`

## Scope

Preserve only the four remaining one-commit Playbook external-smoke branches identified as `export/archive first` in:

- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-EXPORT-ARCHIVE-AND-SMOKE-HOME-MANUAL-REVIEW-DECISION-2026-05-26.md`

In scope:

- `codex/codex-inbox-proof-docs-touch-2`
- `codex/mock-stdin-smoke-nine`
- `codex/mock-watcher-smoke-five`
- `codex/mock-watcher-smoke-six`

Out of scope:

- any branch disposal
- `smoke-home`
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`

## Operating Posture

- ATLAS root remains the coordination and artifact/receipt layer
- preservation and disposal remain separate governance steps
- no owner-repo tracked content was changed
- no external services were touched
- no branches or worktrees were deleted

## Preservation Format

Chosen format:

- `git format-patch --full-index --binary -1`

Reason:

- deterministic
- one file per preserved commit
- directly maps to the one-commit branch structure already classified in the prior decision packet
- easy to review or apply later without reopening branch/worktree disposal in the same lane

## Artifact Packet

Artifact root:

- `packages/patches/playbook-external-smoke-preservation-2026-05-26/`

Manifest:

- `packages/patches/playbook-external-smoke-preservation-2026-05-26/manifest.json`

### Preserved branches

| Branch | Commit | Preserved payload | Artifact |
| --- | --- | --- | --- |
| `codex/codex-inbox-proof-docs-touch-2` | `bce63a8634120189be5a5d379e055d21ed557a9f` | adds `docs/automation/codex-inbox-proof-run.md` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-codex-inbox-proof-docs-touch-2-bce63a86.patch` |
| `codex/mock-stdin-smoke-nine` | `cb77456666c7da45210c6ea655781432d5e8e10a` | adds `mock-stdin-smoke-nine.txt` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-mock-stdin-smoke-nine-cb774566.patch` |
| `codex/mock-watcher-smoke-five` | `c494750e7b3829a3f1f5c5feca8a02c8493c62b2` | adds `mock-watcher-smoke-five.txt` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-mock-watcher-smoke-five-c494750e.patch` |
| `codex/mock-watcher-smoke-six` | `245ed3a4dc13f690703d789783a7f4ad5f81fdf2` | adds `mock-watcher-smoke-six.txt` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-mock-watcher-smoke-six-245ed3a4.patch` |

## Exact Non-Touches

Confirmed unchanged in this pass:

- user-home `smoke-home`
- Playbook stashes
- Lifeline retained worktrees
- active Playbook repo work
- untracked `archive/`

## Owner Boundary Statement

- no tracked Playbook repo files changed
- no Lifeline repo files changed
- no branch/worktree disposal occurred
- no marker changes were justified by this preservation packet

## Post-Preservation Read

What changed:

- the four preservation-first branches now have durable export artifacts under ATLAS-root `packages/patches/`
- their preservation requirement is satisfied by a versioned artifact packet and manifest

What did not change:

- the branches still exist
- `smoke-home` remains a separate manual-review checkout case
- disposal has not been opened

## Recommended Follow-On Packages

1. `Playbook preserved proof/test branch disposal decision`
2. `Playbook smoke-home stranded checkout disposal/manual-review packet`

Recommended ordering:

- decide the post-preservation disposition of the four proof/test branches first
- keep `smoke-home` isolated as its own checkout question second

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `.gitignore`
- `packages/patches/playbook-external-smoke-preservation-2026-05-26/manifest.json`
- `packages/patches/playbook-external-smoke-preservation-2026-05-26/*.patch`
- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-PRESERVATION-EXPORT-PACKET-2026-05-26.md`

## Next Package

`Playbook preserved proof/test branch disposal decision`

Why:

- preservation is now complete
- disposal remains intentionally separate
- `smoke-home` still should not inherit branch-disposal logic
