# ATLAS Target Tree

Audit date: 2026-04-08

This is a logical target tree for portability, rebuildability, and path independence. It is not an instruction to rename or move everything immediately.

```text
C:\ATLAS
+-- stack.yaml                              [relative-path manifest; single source of stack truth]
+-- docs\
|   +-- architecture\                       [stack maps, target tree, boundaries]
|   +-- audits\                             [time-stamped audits and migration plans]
|   `-- standards\                          [cross-stack conventions]
+-- ops\
|   +-- stack\                              [shared operator/workflow surfaces now in _stack]
|   |   +-- codex\
|   |   +-- docs\
|   |   +-- queue\
|   |   +-- receipts\
|   |   +-- scripts\
|   |   `-- templates\
|   `-- manifests\                          [workspace registry and validation maps]
+-- packages\
|   +-- releases\                           [curated distributable packages/tarballs only]
|   `-- bundles\                            [intentional mirror/bundle artifacts]
+-- runtime\
|   +-- codex\                              [logs, worktrees, inbox/archive state]
|   +-- lifeline\                           [local runtime state]
|   +-- playbook\                           [generated indexes/artifacts]
|   +-- logs\
|   `-- receipts\
+-- data\
|   +-- fixtures\                           [checked-in shared test/demo fixtures]
|   +-- snapshots\                          [approved demo snapshots only]
|   `-- exports\                            [stable machine-readable exports]
+-- repos\
|   +-- core\
|   |   +-- atlas\
|   |   +-- lifeline\
|   |   +-- playbook\
|   |   `-- stack-ops\                      [logical destination for _stack]
|   +-- apps\
|   |   +-- fitness\
|   |   +-- mazer\
|   |   `-- nat1-games\
|   +-- research\
|   |   `-- cortex\
|   +-- demos\
|   |   `-- playbook-demo\
|   `-- legacy\
|       +-- mazer-unreal\
|       +-- playbook-v1\
|       +-- hard-pill-drop\
|       +-- realm-blade-drop\
|       `-- backups\
+-- tmp\
|   +-- downloads\
|   +-- local-builds\
|   `-- scratch\
`-- secrets\
    +-- README.md                           [contract only; no secret values in git]
    `-- local\                              [ignored]
```

## Target rules

- Stack truth is rooted at `C:\ATLAS`, but machine-readable paths should be relative to the manifest root rather than hardcoded absolute paths.
- `repos\` should contain canonical source roots, not wrapper folders, installers, videos, zip files, or backup bundles.
- Shared runtime state belongs under `runtime\` or repo-local ignored state, not mixed into source roots without a contract.
- Shared operator assets belong under `ops\`, not split between root-empty `ops\` and active `_stack` source.
- Archive, demo, and legacy content should be clearly partitioned from active repos.
- Every active repo should have the same minimum operator contract: `README.md`, `AGENTS.md`, `.codex\config.toml`, and at least one documented validation entrypoint.

## Migration posture

Phase 1 should normalize manifests and docs without moving source directories.

Phase 2 should standardize contracts and runtime-state placement.

Phase 3 should relocate legacy/demo/binary drops only after manifests, scripts, CI, and local operator commands are proven against the new layout.
