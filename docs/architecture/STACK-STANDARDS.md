# ATLAS Stack Standards

This document is the stack-wide operating contract for ATLAS. It is intentionally concrete.

## 1. Canonical Root

The canonical stack root is the folder that contains:

- `stack.yaml`
- `README-STACK.md`
- `AGENTS.md`
- `repos/`
- `runtime/`
- `data/`
- `packages/`
- `docs/`
- `ops/`
- `tmp/`
- `secrets/`

All stack standards assume commands are evaluated relative to that root.

## 2. Canonical Repo Ids

Use logical ids in stack docs and automation. Current canonical ids:

| Repo id | Current path | Status |
| --- | --- | --- |
| `stack` | `.` | active |
| `_stack` | `repos/_stack` | active |
| `atlas` | `repos/fawxzzy-atlas` | active |
| `playbook` | `repos/playbook` | active |
| `lifeline` | `repos/fawxzzy-lifeline` | active |
| `fitness` | `repos/fawxzzy-fitness` | active |
| `mazer` | `repos/mazer` | active |
| `cortex` | `runtime/cortex` | root-owned subsystem |
| `nat1-games` | `repos/Nat1-Games/nat1-games` | incubating |

Do not hardcode branded disk names into new stack contracts when a repo id is sufficient.

## 3. Path Standard

- Committed stack docs and config must prefer relative paths.
- Machine-specific absolute paths are not canonical.
- A zip extracted on another machine should still preserve the stack contract without search-and-replace.
- Use `/` in docs and config examples unless a Windows-specific path is required.

Good:

- `repos/playbook`
- `docs/architecture/STACK-STANDARDS.md`
- `packages/releases`

Bad:

- `<machine-local-absolute-path>/fawxzzy-playbook`
- `<home>/Desktop/ATLAS`

## 4. Source vs State

`repos/` is for source and source-owned docs only.

Do not treat repo roots as the default home for:

- logs
- screenshots
- exported bundles
- retained runtime state
- machine-local secrets

Use:

- `runtime/` for retained non-secret state
- `tmp/` for disposable outputs
- `packages/` for distributable outputs
- `secrets/` for local secrets

## 5. Export Standard

Every export must have an explicit class and destination:

| Export class | Destination |
| --- | --- |
| patch | `packages/patches` |
| bundle | `packages/bundles` |
| prebuilt output | `packages/prebuilt` |
| release artifact | `packages/releases` |
| source snapshot | `packages/snapshots` |

Default exports must exclude:

- `secrets/**`
- `runtime/**`
- `tmp/**`
- `repos/**/.env`
- `repos/**/.env.*`
- generated dependency and build folders unless explicitly requested

## 6. Runtime Standard

Retained runtime state belongs under clearly named roots:

- `runtime/codex`
- `runtime/atlas`
- `runtime/devservers`
- `runtime/lifeline`
- `runtime/cortex/artifacts`
- `runtime/playbook`
- `runtime/receipts`
- `runtime/state`

If a tool needs repo-specific runtime state, prefer a subfolder under the stack runtime root over a committed repo-root folder.

## 7. Temp Standard

Disposable outputs must go under:

- `tmp/logs`
- `tmp/captures`
- `tmp/previews`
- `tmp/scratch`

If the output is safe to delete and should not ship in a snapshot, it belongs in `tmp/`.

## 8. Governance Baseline Per Active Repo

Each active managed repo should converge on:

- `AGENTS.md`
- `README.md`
- `.codex/config.toml`
- one documented validation entrypoint

The stack control repo is the exception:

- it uses `README-STACK.md` at the root
- it does not require `.codex/config.toml`

Recommended validation names:

- `verify`
- `verify:strict` when a stricter mode exists

If a repo cannot adopt that naming, document the exception in its README and AGENTS file.

For the Wave 1 platform admission surface, use:

- `docs/architecture/atlas-platform-v1.md`
- `docs/architecture/repo-class-admission-rules.md`

For stack-wide validation, prefer ratcheting over one-shot cleanup gates:

- keep a committed baseline artifact for existing stack findings
- fail only on new or expanded `critical` and `error` findings
- keep warnings visible but non-blocking

## 9. Root Session Rule

A session launched from the ATLAS root should default to stack work:

- standards
- audits
- manifests
- packaging policy
- path cleanup
- cross-repo plans

It should not become the default place for editing application code inside active repos.

## 10. Move Order

When structural cleanup is needed, use this order:

1. update standards and manifests
2. fix path-coupled docs and scripts
3. classify material by source, runtime, temp, package, archive, or secret
4. move artifacts and residue out of repo roots
5. validate repo and stack flows
6. only then consider renames or repo moves

## 11. Ingest And Cleanup Guardrails

- Move useful knowledge into ATLAS deliberately, not through blind copy-then-delete sweeps.
- Keep live implementation truth in the owning repo and keep ATLAS references short and pointer-oriented.
- For recovered machine material, prefer manifest-first or selective ingest until the content is classified.
- Delete originals only when they are verified generated trash, dead shims, or safely superseded material.
- See `docs/architecture/ATLAS-INGEST-AND-CLEANUP-GUARDRAILS.md` for the current operating detail.

