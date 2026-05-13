# ATLAS Path Policy

This document defines what belongs in each top-level bucket at the ATLAS root.

## `repos/`

Use for:

- source repositories
- repo-owned source docs
- repo-owned tests and fixtures that are part of source control

Do not use for:

- stack-level standards
- runtime state
- disposable logs or screenshots
- release bundles
- local secrets
- installers, media drops, or backup bundles mixed with active repos

Action:
- Keep active repos at a stable, documented path.
- Treat nested or legacy repos as exceptions to be flattened or archived deliberately, not by accident.

## `runtime/`

Use for:

- retained non-secret state required across sessions
- tool runtime manifests
- inbox runner state
- receipt history
- dev server pid and state files

Do not use for:

- release artifacts
- scratch logs safe to delete
- secrets

Action:
- New runtime-producing tools should take a stack-relative runtime path.
- Runtime data should be safe to remove only with an explicit reset step.

## `data/`

Use for:

- retained non-secret imports
- canonical fixtures shared across tools
- durable exports that are treated as data rather than packages

Do not use for:

- source code
- runtime scratch state
- secrets

Action:
- Organize by purpose, such as `data/imports`, `data/fixtures`, and `data/exports`.

## `packages/`

Use for:

- patches
- bundles
- prebuilt outputs
- releases
- source snapshots

Do not use for:

- repo-local node packages unless ATLAS deliberately creates a true shared package boundary
- secrets
- scratch files

Action:
- Every packaged output must land in an explicit subfolder.
- Do not write release artifacts into `repos/`.

## `docs/`

Use for:

- stack architecture
- audits
- standards
- runbooks
- shared Codex templates

Do not use for:

- repo-specific docs that belong to one repo only
- secret-bearing setup notes

Action:
- Stack contracts should live here even when they reference repos.
- Prefer ATLAS-relative paths in all docs.

## `ops/`

Use for:

- shared bootstrap scripts
- shared validation scripts
- doctor and repair entrypoints
- stack operator utilities that are not repo-owned

Do not use for:

- application source
- repo-specific business logic

Action:
- If an operator script is truly stack-wide, put it here or plan its migration here.
- If the script is repo-specific, keep it in the repo.

## `.github/workflows/`

Use for:

- root-owned orchestration workflows
- QA LLEL CI gate entrypoints that call root scripts
- reusable stack automation that stays generic across repos

Do not use for:

- repo-specific business logic copied out of a child repo
- a second implementation of logic that already lives under `ops/`
- broad authorization for other root `.github/**` surfaces

Action:
- Keep workflow logic thin and script-driven.
- Route behavior through `ops/**` and keep `.github/workflows/**` as orchestration only.

## `tmp/`

Use for:

- logs
- screenshots
- previews
- scratch files
- temporary captures used during debugging

Do not use for:

- retained runtime state
- release outputs
- source files

Action:
- Anything safe to delete after the task should default to `tmp/`.
- New scripts should expose temp output locations explicitly.

## `secrets/`

Use for:

- machine-local secret files
- redacted secret templates
- local-only environment material that must not be exported

Do not use for:

- committed real credentials
- release bundles
- docs examples with live values

Action:
- Keep real secrets under `secrets/local`.
- Keep example shapes under `secrets/templates`.
- Default exports and snapshots must exclude `secrets/**`.

## Global Rules

- New stack contracts must be relative-path first.
- Secrets are excluded from export defaults.
- Runtime state should move outside repos.
- Packaging destinations must be explicit.
- If a file does not clearly belong, classify it before creating it.
- Declared-surface validation is only acceptable when required root governance surfaces remain covered. If a root-owned surface such as `README-STACK.md`, `AGENTS.md`, `.github/workflows/`, `docs/`, or `ops/` falls out of the declared scan set, stack validation must fail rather than silently narrowing governance.
