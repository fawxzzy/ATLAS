# ATLAS Priority Fixes

Audit date: 2026-04-08

## Top 10 fixes in execution order

1. Rewrite `C:\ATLAS\stack.yaml` as the canonical stack registry using root-relative paths and the actual repo set.
2. Freeze a canonical list of active repo roots versus wrappers, demos, legacy repos, and binary drops.
3. Remove old `C:\Users\zjhre\dev\...` workspace assumptions from `repos\_stack\README.md` and `repos\_stack\AGENTS.md`.
4. Reconcile Atlas architecture docs with the actual root layout by removing or clearly redefining the nonexistent `dev/` dispatcher layer.
5. Publish a minimum repo contract for active repos: `README.md`, `AGENTS.md`, `.codex\config.toml`, validation command, and runtime-state policy.
6. Add missing repo contracts where absent or inconsistent: `fawxzzy-atlas`, `fawxzzy-fitness`, `fawxzzy-lifeline`, `fawxzzy-mazer`, and nested app roots such as `Nat1-Games\nat1-games`.
7. Define where generated state belongs and stop mixing screenshots, logs, Playbook indexes, receipts, and temporary files into active repo roots without a rule.
8. Clean the `repos\` namespace by classifying wrappers and nested roots (`Nat1-Games`, `playbook-demo`, `playbook-old`, `mazer-legacy-unreal`) before any moves.
9. Quarantine non-source artifacts from `repos\`: zip files, bundles, installers, videos, and legacy build outputs should move to `packages\`, `data\`, or `repos\legacy\` only after validation.
10. Repair secondary hygiene drift in active repos, including the merge conflict markers in `repos\fawxzzy-playbook\README.md`, after the stack-level contracts are stabilized.

## Risky moves that should wait

- Renaming `fawxzzy-*` directories to shorter names before every manifest, script, and deploy path is converted to relative lookup.
- Moving `_stack` out of its current repo path before its PowerShell runner contracts and package scripts are rewritten and proven.
- Collapsing nested repos (`Nat1-Games\nat1-games`, `playbook-demo\playbook-demo`, `playbook-old\playbookv1`, `mazer-legacy-unreal\Mazer`) before each canonical root is confirmed.
- Deleting or relocating legacy Unreal generated directories (`Binaries`, `DerivedDataCache`, `Intermediate`, `Saved`) before preserving a recovery path and owner intent.
- Purging `.playbook`, `.lifeline`, `.codex`, `.vercel`, screenshots, or preview logs without first deciding which are runtime state, which are fixtures, and which are accidental commits.
- Moving installers, videos, and bundle backups without recording where they will live and whether checksums or provenance matter.
- Touching `secrets\` layout beyond documenting the contract.

## Success criteria for the next structural pass

- One manifest defines the real stack.
- One naming scheme distinguishes active, demo, legacy, and binary-only entries.
- One repo contract exists for every active repo.
- One policy defines where runtime state, generated artifacts, and archives belong.
