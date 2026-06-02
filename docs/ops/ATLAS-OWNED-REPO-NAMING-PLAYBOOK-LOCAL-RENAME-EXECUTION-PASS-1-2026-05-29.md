# Atlas-Owned Repo Naming Playbook Local Rename Execution Pass 1 - 2026-05-29

- Date: `2026-05-29`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `bounded local rename execution`
- Candidate: `repos/fawxzzy-playbook -> repos/playbook`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 78%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-PLAYBOOK-EXECUTION-PREFLIGHT-APPROVAL-2026-05-29.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-REMAINING-FAMILY-DELTA-RECHECK-PASS-7-2026-05-29.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Execute the exact approved local rename only:

- `repos/fawxzzy-playbook -> repos/playbook`

This pass does not:

- rename any remote
- rename any GitHub repo
- reopen any other naming family
- move any marker by itself

## Final Execution Pre-Check

Before rename:

- source path existed: `repos/fawxzzy-playbook`
- destination path was clear: `repos/playbook` did not exist
- `playbook` remained the one honest safe-next candidate
- no exact root-side destination/path blocker remained
- the owner-side watchlist was limited to path-sensitive tests and generated install state only

## Work Performed

Executed in bounded order:

1. renamed the local directory from `repos/fawxzzy-playbook` to `repos/playbook`
2. reconciled exact root-side active path truth in:
   - `stack.yaml`
   - `stack.lock.yaml`
   - `README-STACK.md`
   - `docs/registry/STACK-REPO-INVENTORY.json`
   - `docs/audits/STACK-REPO-INVENTORY.md`
   - `docs/registry/STACK-SYNERGY-REGISTRY.json`
   - `docs/architecture/STACK-STANDARDS.md`
   - `docs/architecture/atlas-current-tree.md`
   - `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
   - `docs/memory/initiatives/continuity-manifest-atlas-owned-repo-naming-canonicalization.json`
   - `ops/atlas/build_codex_context.py`
   - `ops/atlas/continuity.py`
   - `ops/atlas/qa/adapters/playbook.docs.json`
   - `ops/atlas/qa/scenarios/playbook.docs-governance.json`
   - `ops/atlas/qa/templates/docs-only/template.docs-only.json`
   - `ops/atlas/qa/templates/docs-only/template.docs-only.verify.json`
   - `data/fixtures/atlas.playbook.adoption.report.example.v1.json`
   - `tests/test_atlas_codex_context.py`
   - `ops/validation/stack-validation.baseline.json`
3. regenerated canonical lock and published inventory surfaces after the path move
4. restored the adjacent excluded-surface identity `repos/fawxzzy-playbook-codex` after an over-broad initial exact-string replacement

Replacement discipline used:

- exact active local-path truth moved from `repos/fawxzzy-playbook` to `repos/playbook`
- bare `fawxzzy-playbook` remote/project identity strings were left alone unless they were asserting the active local path
- adjacent helper identity `repos/fawxzzy-playbook-codex` was preserved as-is

## Filesystem Result

After rename:

- `repos/fawxzzy-playbook`: absent
- `repos/playbook`: present
- `repos/playbook` repo status: `main...origin/main [behind 7]`

## Exact Execution Breaks Surfaced

Two exact breaks surfaced during the cluster:

1. root-side over-rewrite on the excluded adjacent helper surface:
   - `repos/fawxzzy-playbook-codex` was incorrectly rewritten to `repos/playbook-codex`
   - fixed inside the cluster before proof closeout
2. owner-side generated install state break:
   - `pnpm playbook verify --json` and `pnpm playbook docs audit --json` failed immediately after rename because workspace package resolution still pointed through stale generated `node_modules` state at the old path
   - this was a real post-rename owner-side break and moved into the conditional owner-side fix lane

## Packet Status

Execution status after this pass:

- `executed`

Proof / reconciliation status after this pass:

- `in progress in the same cluster`

## Rule

One candidate, one cluster, one reconciliation.

## Failure Mode

Renaming the directory without correcting the adjacent helper-surface over-rewrite and the generated install-state break would create a false-durable packet even though the filesystem move itself succeeded.
