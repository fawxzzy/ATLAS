# ATLAS Current Tree

Audit date: 2026-04-08

Normalized current tree, excluding `node_modules`, build output, and secret contents.

```text
ATLAS root
+-- stack.yaml                              [root stack manifest; stale absolute paths]
+-- data\                                   [empty]
+-- docs\
|   +-- architecture\
|   `-- audits\
+-- ops\                                    [empty]
+-- packages\                               [empty]
+-- repos\
|   +-- .vercel\                            [workspace/platform metadata]
|   +-- _stack\                             [active operator/workflow repo]
|   |   +-- docs\
|   |   +-- ops\
|   |   +-- queue\
|   |   +-- receipts\
|   |   +-- templates\
|   |   +-- .codex\                         [runner state; no repo-local config.toml]
|   |   +-- AGENTS.md
|   |   +-- README.md
|   |   +-- package.json
|   |   `-- workspace.manifest.json
|   +-- cortex\                             [active Python framework snapshot]
|   |   +-- core\
|   |   +-- docs\
|   |   +-- nexus\
|   |   +-- plugins\
|   |   +-- .codex\
|   |   +-- AGENTS.md
|   |   +-- README.md
|   |   +-- requirements.txt
|   |   +-- setup.py
|   |   `-- validate_repo.py
|   +-- fawxzzy-atlas\                      [active architecture/docs repo]
|   |   +-- docs\
|   |   `-- README.md
|   +-- fawxzzy-fitness\                    [active Next.js app]
|   |   +-- .codex\                         [present; no config.toml observed]
|   |   +-- .github\
|   |   +-- .githooks\
|   |   +-- .lifeline\
|   |   +-- .playbook\
|   |   +-- assets\
|   |   +-- docs\
|   |   +-- public\
|   |   +-- scripts\
|   |   +-- src\
|   |   +-- supabase\
|   |   +-- tests\
|   |   +-- AGENT.md                        [non-standard singular name]
|   |   +-- README.md
|   |   `-- package.json
|   +-- fawxzzy-lifeline\                   [active TypeScript CLI/runtime operator repo]
|   |   +-- .codex\                         [present; no config.toml observed]
|   |   +-- .github\
|   |   +-- .lifeline\
|   |   +-- .playbook\
|   |   +-- docs\
|   |   +-- examples\
|   |   +-- fixtures\
|   |   +-- Playbook\
|   |   +-- scripts\
|   |   +-- src\
|   |   +-- README.md
|   |   `-- package.json
|   +-- fawxzzy-mazer\                      [active Vite/TypeScript/Phaser app]
|   |   +-- docs\
|   |   +-- legacy\
|   |   +-- public\
|   |   +-- src\
|   |   +-- tests\
|   |   +-- AGENTS.md
|   |   +-- README.md
|   |   `-- package.json
|   |       note: repo root also contains committed screenshots/logs/temp files
|   +-- fawxzzy-playbook\                   [active Playbook monorepo]
|   |   +-- .codex\                         [has config.toml]
|   |   +-- .github\
|   |   +-- .husky\
|   |   +-- .lifeline\
|   |   +-- .playbook\
|   |   +-- actions\
|   |   +-- architecture\
|   |   +-- docs\
|   |   +-- exports\
|   |   +-- fixtures\
|   |   +-- packages\
|   |   +-- patterns\
|   |   +-- playbook\
|   |   +-- rules\
|   |   +-- scripts\
|   |   +-- subapps\
|   |   +-- templates\
|   |   +-- test\
|   |   +-- tests\
|   |   +-- AGENTS.md
|   |   +-- README.md                       [contains merge conflict markers]
|   |   `-- package.json
|   +-- Hard Pill To Swallow\              [binary/install drop; no repo contract]
|   |   `-- BigPaperGodzillas_HardPillToSwallow_GoldBuild\
|   +-- mazer-legacy-unreal\               [legacy Unreal project wrapper]
|   |   `-- Mazer\                          [actual project root]
|   +-- Nat1-Games\                        [mixed parent + nested actual repo]
|   |   +-- .playbook\                      [generated state at parent]
|   |   +-- .playbookignore
|   |   `-- nat1-games\                     [actual Vite/React app root]
|   +-- playbook-demo\                     [wrapper around nested demo repo]
|   |   `-- playbook-demo\                  [actual repo root]
|   +-- playbook-old\                      [wrapper around nested legacy repo]
|   |   `-- playbookv1\                     [actual repo root]
|   +-- Realm Blade\                       [binary/media drop; no repo contract]
|   +-- repo-backups\                      [bundle/patch backup drop]
|   +-- .gitignore
|   +-- AGENTS.md
|   +-- CORTEX-AND-PLAYBOOK-20260408.zip
|   +-- dev.zip
|   `-- mazer-legacy-unreal.zip
+-- runtime\                               [empty]
+-- secrets\                               [present; contents intentionally not inspected]
`-- tmp\                                   [empty]
```

## Current classification

| Path | Observed role | Confidence | Notes |
| --- | --- | --- | --- |
| `repos\_stack` | Workspace operator/workflow repo | High | PowerShell/Codex runner surfaces and workspace manifest. |
| `repos\cortex` | Python framework snapshot | High | README, setup.py, validate script, docs. |
| `repos\fawxzzy-atlas` | Architecture/docs repo | High | Docs-first README and stack-boundary docs. |
| `repos\fawxzzy-fitness` | Next.js fitness app | High | `package.json`, `src`, `public`, Supabase, tests. |
| `repos\fawxzzy-lifeline` | TypeScript CLI for local operator/runtime | High | CLI `bin`, examples, fixtures, large smoke suite. |
| `repos\fawxzzy-mazer` | Rebuilt game/app in Vite + Phaser | High | README and package manifest. |
| `repos\fawxzzy-playbook` | Playbook monorepo/runtime | High | Monorepo packages, docs, CLI scripts. |
| `repos\Hard Pill To Swallow` | Binary build/install drop | Medium | Installer and video only. |
| `repos\mazer-legacy-unreal\Mazer` | Legacy Unreal source project | High | `.uproject`, `.sln`, Unreal directories. |
| `repos\Nat1-Games\nat1-games` | App repo nested inside wrapper | Medium | `package.json`, app folders, Playwright, API. |
| `repos\playbook-demo\playbook-demo` | Playbook demo fixture repo | High | README explicitly describes demo purpose. |
| `repos\playbook-old\playbookv1` | Legacy Playbook v1 repo | High | README explicitly describes older governance engine. |
| `repos\Realm Blade` | Binary/media drop | Medium | Installer and gameplay videos only. |
| `repos\repo-backups` | Backup artifacts | High | `.bundle` and `.patch` only. |

## Cross-cutting observations

- Root support directories (`runtime`, `data`, `packages`, `ops`, `tmp`) are empty today.
- Operational state is still scattered inside repos (`.playbook`, `.lifeline`, `.codex`, screenshots, logs, preview artifacts, receipts).
- Several entries under `repos\` are wrappers, drops, or archives rather than canonical repo roots.
- The stack currently mixes active source repos, legacy source repos, build outputs, installers, media, and zip/bundle backups in the same namespace.
