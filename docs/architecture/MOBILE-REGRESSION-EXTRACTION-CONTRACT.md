# Mobile Regression Extraction Contract

## Reviewed / Readiness / Evidence

- Reviewed: `2026-04-11`
- Readiness: `phase-1 promote now`
- Evidence class: `live code + live fixtures + live tests`
- Scope: `mobile-regression` is the manifest-driven review-board and fixture-contract lane that survived inside live Fitness repo code, not the whole mobile app surface.

## Canonical Sources

Primary sources:

- `repos/fawxzzy-fitness/scripts/build-mobile-regression-boards.py`
- `repos/fawxzzy-fitness/docs/mobile-regression-fixtures.md`

Supporting boundary files:

- `repos/fawxzzy-fitness/scripts/qa-matrix.mjs`
- `repos/fawxzzy-fitness/src/lib/dev/mobileRegressionFixtures.ts`
- `repos/fawxzzy-fitness/src/lib/dev/mobileRegressionContracts.ts`
- `repos/fawxzzy-fitness/src/lib/dev/mobile-regression-fixtures.test.ts`
- `repos/fawxzzy-fitness/tests/mobile-fixtures/mobile-regression-inventory.test.ts`
- `repos/fawxzzy-fitness/tests/visual-regression/mobile-regression-contracts.test.ts`

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
- Fixture inventory comes from `mobileRegressionScenarios` in `src/lib/dev/mobileRegressionFixtures.ts`.
- The board builder accepts an optional manifest path override.
- The capture lane accepts optional scenario selectors as `scenario.id` or `screen:fixture`.

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
- `npm run test:mobile-regression-fixtures`

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
- Fixture inventory and manifest compatibility stay aligned with the live Fitness contract surface during extraction.

Current tests:

- `src/lib/dev/mobile-regression-fixtures.test.ts` validates scenario IDs, family mapping, contract checks, and stable screen/fixture lookup pairs.
- `tests/mobile-fixtures/mobile-regression-inventory.test.ts` validates route coverage, floating-header usage, and retained hardening fixtures.
- `tests/visual-regression/mobile-regression-contracts.test.ts` validates that known geometry and state regressions trip the contract helpers.

Missing tests:

- No direct test currently exercises `build-mobile-regression-boards.py`.
- No malformed-manifest contract test exists for the Python surface.
- No golden-image assertion exists for board layout output.

## Dependencies

Runtime dependencies:

- Python 3
- Pillow
- Node
- Repo-local browser launch support for the capture step

File dependencies:

- `src/lib/dev/mobileRegressionFixtures.ts`
- `src/lib/dev/mobileRegressionContracts.ts`
- `.codex/qa/mobile-regression/manifest.json`
- `.codex/qa/mobile-regression/*.png`

External assets:

- Live application routes under `/dev/mobile-regression`
- Browser executable resolved by the capture lane

## Gaps

- The surviving script is a validated successor, not an exact filename recovery of `build_mobile_regression_board.py`.
- The surviving Markdown doc is a partial equivalent, not a recovered text README.
- The Python board builder still lacks direct contract coverage, malformed-manifest tests, and golden-image layout assertions.

## Promotion Target

- Proposed ATLAS module name: `mobile-regression`
- ATLAS contract record: `docs/architecture/MOBILE-REGRESSION-EXTRACTION-CONTRACT.md`
- Shared sample payloads should later normalize under `data/fixtures/mobile-regression/`

Minimal refactor needed before promotion:

- Extract the board-builder and fixture-contract helpers as an explicitly owned boundary inside `fawxzzy-fitness`.
- Add direct contract coverage for the Python board-builder surface.
- Add malformed-manifest tests for the Python surface.
- Add a golden-image assertion for board layout output.
- Keep manifest parsing, review-family ordering, artifact names, fixture inventory, and contract validation helpers stable during extraction.

## Operational Caveat

- The manifest and descendant evidence are internally consistent, but the search and manifold pass was produced by directly executing prompt bodies because the local `codex.exe` path returned `Access is denied`.
- That provenance makes this a strong extraction-planning artifact, not proof of a fully verified trusted Codex CLI session.
- When returning to the CLI verification layer, current Codex docs indicate that project-scoped `.codex/config.toml` only loads for trusted projects, CLI flags override config, and `/sandbox-add-read-dir` is the Windows-native command for temporary sandbox read access.
