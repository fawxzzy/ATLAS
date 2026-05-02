# Automated Changelog Generator Plan

## Scope

This is a stack-level routing and implementation plan only.

- ATLAS root remains the coordination layer.
- Implementation should not land in the ATLAS root.
- The owner repo for this feature should be `repos/fawxzzy-playbook`.

## Why Playbook Owns This

`fawxzzy-playbook` is the lowest-risk home for a repo-agnostic changelog generator because it already provides:

- a repo-agnostic local CLI surface in TypeScript
- a modular split between CLI and engine packages
- existing release planning and sync behavior
- existing changelog and release-note conventions
- local-first verification and package publishing workflows

The current stack root and `_stack` repos are operator surfaces, not the right place to host changelog generation logic.

## Detected Stack

Target repo: `repos/fawxzzy-playbook`

- Language: TypeScript on Node.js
- Package manager: `pnpm@10.23.0`
- Engine requirement: `node >=22`
- Test framework: `vitest`
- Linting: `eslint`
- CLI convention: `packages/cli/src/commands/**`, surfaced through `pnpm playbook ...`
- Engine/domain convention: `packages/engine/src/**`
- Docs conventions: `README.md`, `docs/**`, `docs/CHANGELOG.md`, `docs/RELEASING.md`
- Existing release automation: `.github/workflows/release-prep.yml`, `.github/workflows/publish-npm.yml`

## Existing Release And Changelog Conventions

Playbook already has three relevant surfaces:

1. `CHANGELOG.md`
   Uses top-level `WHAT` and `WHY` sections in the unreleased area.

2. `docs/CHANGELOG.md`
   Contains a managed release-notes block with version headings and `WHAT`/`WHY` bullets.

3. `playbook release`
   Existing CLI and engine support deterministic release planning and release drift sync.

Because of those existing contracts, the changelog generator should be implemented as a release-adjacent capability inside Playbook rather than as a brand-new standalone repo.

## Recommended Module Boundaries

Prefer a package split that matches existing Playbook architecture.

Engine package:

- `packages/engine/src/release/changelog/types.ts`
- `packages/engine/src/release/changelog/config.ts`
- `packages/engine/src/release/changelog/collectors/git.ts`
- `packages/engine/src/release/changelog/classifier.ts`
- `packages/engine/src/release/changelog/entryBuilder.ts`
- `packages/engine/src/release/changelog/renderers/markdown.ts`
- `packages/engine/src/release/changelog/renderers/json.ts`
- `packages/engine/src/release/changelog/append.ts`
- `packages/engine/src/release/changelog/validate.ts`
- `packages/engine/src/release/changelog/index.ts`

CLI package:

- `packages/cli/src/commands/changelog/index.ts`
- `packages/cli/src/commands/changelog/index.test.ts`

Integration/export surfaces:

- `packages/engine/src/index.ts`
- Playbook CLI command router files already used to register command families

Tests:

- `packages/engine/src/release/changelog/*.test.ts`
- fixture helpers under a release/changelog test subfolder if needed

Docs:

- `docs/commands/README.md`
- `docs/RELEASING.md`
- `docs/CHANGELOG.md`
- `README.md` only if command discovery or onboarding changes

## Implementation Shape

Build this as a deterministic local CLI first.

Required phases:

1. Collect git changes from local history.
2. Classify changes with explainable rules.
3. Convert classified changes into normalized `WHAT` + `WHY` entries.
4. Render Markdown and JSON.
5. Add append and validate workflows.
6. Add CI only after local CLI behavior is stable.

Do not make GitHub Actions or GitHub API the source of truth.

## Recommended Commands

Command family should be:

- `pnpm playbook changelog generate --from <ref> --to <ref> --format markdown`
- `pnpm playbook changelog generate --from <ref> --to <ref> --format json`
- `pnpm playbook changelog append --from <ref> --to <ref> --file CHANGELOG.md`
- `pnpm playbook changelog validate --from <ref> --to <ref>`

If command-surface pressure is high, the fallback is a `playbook release changelog ...` subcommand tree, but a first-class `changelog` command is easier to keep modular.

## PR-Sized Lanes

### Wave 0: Operator unblock

Before unattended `_stack`-launched Codex runs can implement this in Playbook, widen the Playbook `_stack` adapter.

Current blocker:

- `repos/_stack/ops/codex/repos/playbook/adapter.json` only allows mutations in:
  - `.codex/**`
  - `README.md`
  - `docs/**`
  - `scripts/codex-*.ps1`

That adapter currently forbids mutations in `packages/cli/**`, `packages/engine/**`, `.github/**`, and most scripts. The prompt chain can run today only in a repo-local Playbook session, not through the current unattended `_stack` implementation runner.

Recommended minimal adapter expansion for this project:

- `packages/cli/**`
- `packages/engine/**`
- `.github/workflows/**`
- `scripts/**`

Keep the expansion narrow and changelog-specific if the runner remains governance-sensitive.

### Wave 1: Low-conflict foundations

Lane 1: domain model and config

- Own `types.ts`, `config.ts`, package exports, and config tests.

Lane 2: git collector

- Own `collectors/git.ts` and its tests.

Lane 3: classifier

- Own `classifier.ts` and its tests.

Lane 4: entry builder and renderers

- Own `entryBuilder.ts`, `renderers/**`, and renderer tests.

Lane 5: docs skeleton

- Own docs only. Do not claim implementation is complete.

### Wave 2: Integration and hardening

Lane 6: CLI wiring

- Own `packages/cli/src/commands/changelog/**`
- Wire engine exports into the CLI
- Add command tests

Lane 7: append and validate

- Own append/validate engine modules plus CLI integration

Lane 8: full fixture suite

- Add end-to-end and fixture-driven tests

Lane 9: CI integration

- Add the smallest safe workflow addition

Lane 10: final polish

- Tighten docs, exports, diagnostics, and determinism

## Checkpoints

Checkpoint 1: after Wave 0

- Owner repo confirmed
- unattended runner path either widened or explicitly deferred

Checkpoint 2: after Wave 1

- engine primitives merged
- no CLI/file-mutation overlap left unresolved

Checkpoint 3: after Wave 2 integration

- CLI commands work locally
- append is safe
- validate produces actionable output

Checkpoint 4: final hardening

- targeted tests pass
- docs are honest
- CI uses the local CLI rather than parallel logic

## Verification Expectations

For Playbook implementation work, use repo-local verification rather than root verification.

Minimum per implementation PR:

- `pnpm -r build`
- targeted `vitest` coverage for touched modules

For CLI or docs-command changes also run:

- `pnpm agents:update`
- `pnpm agents:check`
- `pnpm playbook docs audit --json`

For final integration:

- `pnpm verify`

The ATLAS root session should only verify that this plan remains consistent with stack routing and path policy.

## Risks

- `_stack` unattended Codex execution is currently blocked by Playbook adapter mutation limits.
- Playbook already has release planning logic, so naming and responsibility overlap with `release` must stay explicit.
- Existing `CHANGELOG.md` and `docs/CHANGELOG.md` formats are related but not identical; append behavior must choose the right target contract.
- A single giant `packages/engine/src/release/index.ts` already exists. Changelog logic should be added as submodules, not piled into that file.

## Assumptions

- The initial implementation should be local-git-first and deterministic.
- GitHub PR metadata is optional future enrichment, not a prerequisite.
- The CLI should remain dependency-light and prefer existing Playbook tooling patterns.

## Open Questions

- Should changelog generation be a first-class `playbook changelog` command or a `playbook release changelog` subtree?
- Should append target `CHANGELOG.md`, `docs/CHANGELOG.md`, or both with separate modes?
- Should repo-specific classification rules live in a checked-in config file or in Playbook release policy alongside existing version governance?
- Is widening the `_stack` Playbook adapter acceptable, or should Wave 1 happen only in direct Playbook repo sessions?

## Recommended Next Runs

1. Root session:
   Narrowly update `_stack` Playbook adapter permissions if unattended source mutation is required.

2. Playbook repo session:
   Run architecture-only Prompt 0 against `repos/fawxzzy-playbook` and write the repo-local plan.

3. Playbook repo session:
   Run Wave 1 lanes in parallel with disjoint ownership:
   - domain/config
   - git collector
   - classifier
   - entry builder/renderers
   - docs

4. Playbook repo session:
   Merge Wave 1, then run Wave 2 integration and hardening.
