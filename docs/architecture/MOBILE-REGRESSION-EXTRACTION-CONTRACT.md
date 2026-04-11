# Mobile Regression Extraction Contract

## Reviewed / Readiness / Evidence

- Reviewed: `2026-04-11`
- Readiness: `phase-1 promote now`
- Evidence class: `live code + live fixtures + live tests`
- Scope: `mobile-regression` is the manifest-driven review-board and fixture-contract lane that survived inside live Fitness repo code, not the whole mobile app surface.

## Canonical Sources

Primary implementation sources:

- `repos/fawxzzy-fitness/src/features/mobile-regression/fixtures.ts`
- `repos/fawxzzy-fitness/src/features/mobile-regression/contracts.ts`
- `repos/fawxzzy-fitness/scripts/mobile_regression/board_builder.py`
- `repos/fawxzzy-fitness/src/app/dev/mobile-regression/page.tsx`
- `repos/fawxzzy-fitness/scripts/qa-matrix.mjs`
- `repos/fawxzzy-fitness/docs/mobile-regression-fixtures.md`

Public CLI shim:

- `repos/fawxzzy-fitness/scripts/build-mobile-regression-boards.py`

Supporting tests:

- `repos/fawxzzy-fitness/tests/mobile-regression/fixtures.test.ts`
- `repos/fawxzzy-fitness/tests/mobile-regression/inventory.test.ts`
- `repos/fawxzzy-fitness/tests/mobile-regression/build-mobile-regression-boards.test.ts`
- `repos/fawxzzy-fitness/tests/mobile-regression/contracts.test.ts`
- `repos/fawxzzy-fitness/tests/mobile-regression/README.md`

Temporary compatibility shims:

- `repos/fawxzzy-fitness/src/lib/dev/mobileRegressionFixtures.ts`
- `repos/fawxzzy-fitness/src/lib/dev/mobileRegressionContracts.ts`

## Purpose

- Turn deterministic mobile screenshot captures into review-board PNGs for regression triage.
- Preserve the strongest near-match lineage that survived in `fawxzzy-fitness`.
- Keep Phase 1 scoped to the board-builder, manifest, fixture inventory, and contract validators rather than the full mobile application.

## Inputs

- Primary manifest input: `repos/fawxzzy-fitness/.codex/qa/mobile-regression/manifest.json`
- Alternate manifest input: `python scripts/build-mobile-regression-boards.py [manifest_path]`
- Manifest shape includes `generatedAt`, `baseUrl`, `viewportHeight`, `widths[]`, and `scenarios[]`.
- Each scenario currently carries `id`, `name`, `family`, `route`, `screen`, `fixture`, and `captures[]`.
- Screenshot payloads must exist beside the manifest and currently follow `{scenario-id}-{width}.png`.
- Fixture inventory comes from `mobileRegressionScenarios` in `src/features/mobile-regression/fixtures.ts`.
- The board builder accepts an optional manifest path override.
- The capture lane accepts optional scenario selectors as `scenario.id` or `screen:fixture`.
- The public CLI entrypoint still runs through `scripts/build-mobile-regression-boards.py`, which is now a thin shim over `scripts/mobile_regression/board_builder.py`.

Environment assumptions:

- Python 3 is available.
- Pillow is installed for board rendering.
- Node is available for the capture lane.
- The target app is reachable at `QA_BASE_URL` or the repo default.
- The capture lane can launch a Chromium-family browser through the repo-local Edge workflow.

## Outputs

Generated review boards:

- `mega-board.png`
- `exercise-cards-board.png`
- `session-logging-board.png`
- `session-summaries-board.png`
- `settings-detail-board.png`

Generated capture artifacts:

- `.codex/qa/mobile-regression/manifest.json`
- `.codex/qa/mobile-regression/*.png`

Metadata and logs:

- `qa-matrix.mjs` prints one console line per scenario-width capture and a final manifest-write line.
- The Python board builder writes files without a separate structured log artifact.

Current failure modes:

- Missing manifest raises `FileNotFoundError`.
- Missing screenshot file raises `FileNotFoundError`.
- Empty scenario inventory raises `ValueError`.
- Unknown review family raises `ValueError`.
- Capture failures bubble up from the browser process and stop manifest generation.

## Public Surface

CLI entrypoints:

- `npm run qa:matrix`
- `npm run qa:boards`
- `npm run test:mobile-regression-fixtures` (includes the CLI-boundary board-builder harness in `tests/mobile-regression/build-mobile-regression-boards.test.ts`)

Direct callable surfaces:

- `getMobileRegressionScenarioById(id)`
- `resolveMobileRegressionScenario({ scenario, screen, fixture })`
- `validateMobileScenarioContracts(scenario)`

Config knobs already in use:

- `QA_BASE_URL`
- `QA_WIDTHS`
- `QA_HEIGHT`
- `QA_CAPTURE_DELAY_MS`
- `QA_EDGE_PATH`
- board-builder manifest path argv override

## Fixtures And Tests

Sample manifest:

- `repos/fawxzzy-fitness/.codex/qa/mobile-regression/manifest.json`

Stable expectations:

- Current review-family board names stay as listed above.
- Current family ordering comes from the live script and companion doc.
- Fixture inventory and manifest compatibility stay aligned with the extracted Fitness contract surface during downstream consolidation.

Current tests:

- `tests/mobile-regression/fixtures.test.ts` validates scenario IDs, family mapping, contract checks, and stable screen/fixture lookup pairs.
- `tests/mobile-regression/inventory.test.ts` validates route coverage, floating-header usage, and retained hardening fixtures.
- `tests/mobile-regression/build-mobile-regression-boards.test.ts` directly exercises `scripts/build-mobile-regression-boards.py` through the CLI boundary, verifies the named board set, locks deterministic PNG hashes for canonical output, and covers malformed-manifest, unknown-family, missing-screenshot, and missing-manifest failures while the shim delegates into `scripts/mobile_regression/board_builder.py`.
- `tests/mobile-regression/contracts.test.ts` validates that known geometry and state regressions trip the contract helpers.

## Dependencies

Runtime dependencies:

- Python 3
- Pillow
- Node
- Repo-local browser launch support for the capture step

File dependencies:

- `src/features/mobile-regression/fixtures.ts`
- `src/features/mobile-regression/contracts.ts`
- `src/app/dev/mobile-regression/page.tsx`
- `scripts/mobile_regression/board_builder.py`
- `scripts/qa-matrix.mjs`
- `.codex/qa/mobile-regression/manifest.json`
- `.codex/qa/mobile-regression/*.png`

External assets:

- Live application routes under `/dev/mobile-regression`
- Browser executable resolved by the capture lane

## Gaps

- The extraction already landed: the feature boundary lives under `src/features/mobile-regression`, and board construction lives in `scripts/mobile_regression/board_builder.py`.
- Remaining work is downstream import and call-site consolidation onto `src/features/mobile-regression/*` and `scripts/mobile_regression/board_builder.py` while compatibility shims remain in place.
- Deliberate shim removal is still pending for `src/lib/dev/mobileRegressionFixtures.ts` and `src/lib/dev/mobileRegressionContracts.ts` after downstream callers are clean.
- Historical filename/doc provenance and future work around checked-in sample-manifest provenance, extraction packaging, or environment-hardening remain follow-on concerns, not blockers for treating the boundary as already extracted.

## Promotion Target

- Proposed ATLAS module name: `mobile-regression`
- ATLAS contract record: `docs/architecture/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md`
- Shared sample payloads should later normalize under `data/fixtures/mobile-regression/`

Promotion posture:

- The board-builder and fixture-contract helpers are already extracted as an explicitly owned boundary inside `fawxzzy-fitness`.
- Treat `src/features/mobile-regression/*` and `scripts/mobile_regression/board_builder.py` as the canonical promotion shape.
- Finish downstream import and call-site consolidation while keeping the public CLI shim and temporary compatibility shims stable for callers that still depend on them.
- Remove the temporary shims only after caller cleanup is complete, while keeping manifest parsing, review-family ordering, artifact names, fixture inventory, and contract validation helpers stable through that transition.

## Operational Caveat

- The manifest and descendant evidence are internally consistent, but the search and manifold pass was produced by directly executing prompt bodies because the local `codex.exe` path returned `Access is denied`.
- That provenance makes this a strong extraction-planning artifact, not proof of a fully verified trusted Codex CLI session.
- When returning to the CLI verification layer, current Codex docs indicate that project-scoped `.codex/config.toml` only loads for trusted projects, CLI flags override config, and `/sandbox-add-read-dir` is the Windows-native command for temporary sandbox read access.
