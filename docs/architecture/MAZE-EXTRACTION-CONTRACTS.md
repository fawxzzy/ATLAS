# Maze Extraction Contracts

## Reviewed / Readiness / Evidence

- Reviewed: `2026-04-11`
- Readiness: `phase-2 refactor first`
- Evidence class: `live code + shared domain tests`
- Scope: `maze-pattern-engine` and `maze-batch` are living descendants in `fawxzzy-mazer`, not exact historical recoveries.

## Shared Preamble

- `maze-pattern-engine` and `maze-batch` remain Phase 2 candidates.
- Neither candidate should be promoted until it has a dedicated source boundary and dedicated contract tests.
- Both candidates currently depend on shared maze-domain code and shared maze-domain verification.
- Keep both candidates framed as modern extracted descendants from live code, not exact legacy-file recoveries.

## `maze-pattern-engine`

### Canonical Sources

Primary sources:

- `repos/fawxzzy-mazer/src/domain/maze/core.ts`
- `repos/fawxzzy-mazer/src/domain/maze/types.ts`
- `repos/fawxzzy-mazer/tests/maze/maze-domain.test.ts`

Supporting boundary files:

- `repos/fawxzzy-mazer/src/domain/maze/index.ts`
- `repos/fawxzzy-mazer/src/domain/maze/generator.ts`

### Purpose

- Drive deterministic rotating maze presentation frames over generated `MazeEpisode` values.
- Define the smallest reusable boundary that can later be promoted out of the oversized maze core surface.

### Inputs

Constructor inputs:

- `makeMaze: () => MazeEpisode`
- `mode: PatternEngineMode`
- optional `cortex: CortexSink`

Runtime inputs:

- `next(dtSeconds)` advances the current frame clock and may rotate to a fresh frame.
- `suspend()`, `resumeFresh()`, and `destroy()` control lifecycle.

Environment assumptions:

- The caller supplies valid `MazeEpisode` objects.
- The caller supplies deterministic episode generation if replay stability matters.
- Callers respect disposal semantics when holding frames beyond engine lifetime.

### Outputs

Primary output:

- `PatternFrame` objects with `mode`, `episode`, and `t`

Side effects:

- Optional `cortex.push(toCortexSample(frame.episode))` when a sink is present.
- `destroy()` disposes the current episode and clears engine state.

Current behavioral guarantees from live code:

- The first `next()` lazily creates the initial frame.
- Suspended engines do not advance elapsed time.
- `resumeFresh()` clears hidden-tab backlog by dropping the current frame.
- `demo`, `loading`, `idle`, and `kiosk` use different advance timing rules.

Current failure modes:

- No guard exists against a throwing `makeMaze` factory.
- No guard exists against negative or nonsensical `dtSeconds`.
- Callers that never call `destroy()` can retain episode memory longer than intended.

### Public Surface

Public class:

- `new PatternEngine(makeMaze, mode, cortex?)`

Public methods:

- `next(dtSeconds): PatternFrame`
- `suspend(): void`
- `resumeFresh(): void`
- `destroy(): void`

Exported types tied to the contract:

- `PatternFrame`
- `PatternEngineMode`
- `CortexSink`
- `MazeEpisode`

### Fixtures And Tests

Sample verification path:

- `repos/fawxzzy-mazer/tests/maze/maze-domain.test.ts`

Current tests:

- The domain suite verifies `resumeFresh()` by suspending an engine, simulating hidden-tab time, resuming, and asserting a fresh frame with advanced seed or cycle state.
- The domain suite also exercises deterministic generation surfaces that the engine depends on.

Expected outputs:

- Resuming should create a new frame rather than replaying accumulated backlog.
- `destroy()` should dispose the current episode.

Missing tests:

- No dedicated `pattern-engine` test file exists.
- No isolated constructor or input-validation tests exist.
- No dedicated Cortex emission test exists outside the broad domain suite.

### Dependencies

Runtime dependencies:

- TypeScript and Vitest toolchain in `fawxzzy-mazer`

File dependencies:

- `src/domain/maze/core.ts`
- `src/domain/maze/types.ts`
- `src/domain/maze/generator.ts`

Implicit behavioral dependencies:

- `disposeMazeEpisode()`
- `toCortexSample()`
- `resolveDemoFrameDuration()`

### Gaps

- `PatternEngine` is embedded inside `core.ts` beside unrelated maze generation, solving, and topology logic.
- Verification still lives in a shared maze-domain suite instead of a dedicated module contract.
- The candidate still lacks isolated constructor, lifecycle, and Cortex-emission coverage.

### Promotion Target

- Proposed ATLAS module name: `maze-pattern-engine`
- ATLAS contract record: `docs/architecture/MAZE-EXTRACTION-CONTRACTS.md`

Minimal refactor needed before promotion:

- Move `PatternEngine` and its directly required helpers into a dedicated source file.
- Add a standalone contract test file for lifecycle, backlog dropping, and optional Cortex emission.
- Keep this candidate in Phase 2 until the source boundary and contract tests exist.

### Operational Caveat

- This descendant-validation pass is strong planning evidence, but not a fully trusted nested Codex CLI proof while the local `codex.exe` path still returns `Access is denied`.
- When returning to the CLI verification layer, current Codex docs indicate that project-scoped `.codex/config.toml` only loads for trusted projects, CLI flags override config, and `/sandbox-add-read-dir` is the Windows-native command for temporary sandbox read access.

## `maze-batch`

### Canonical Sources

Primary sources:

- `repos/fawxzzy-mazer/src/domain/maze/batch.ts`
- `repos/fawxzzy-mazer/src/domain/maze/types.ts`
- `repos/fawxzzy-mazer/tests/maze/maze-domain.test.ts`

Supporting boundary files:

- `repos/fawxzzy-mazer/src/domain/maze/core.ts`
- `repos/fawxzzy-mazer/src/domain/maze/generator.ts`
- `repos/fawxzzy-mazer/src/domain/maze/index.ts`

### Purpose

- Run repeated maze builds across a deterministic seed sequence and summarize aggregate topology and difficulty metrics.
- Define a narrow extraction boundary for batch sampling and optional Cortex emission apart from the full maze domain.

### Inputs

Function signature:

- `runBatch(runs = 100, width = 50, height = 50, braidRatio = 0.08, cortex?)`

Internal deterministic inputs:

- Seeds advance as `iteration + 1`.
- `minSolutionLength` is derived from the smaller board dimension.

Environment assumptions:

- The caller supplies positive run and dimension counts.
- `buildMaze()` remains available and behaviorally compatible.
- The optional Cortex sink accepts `push(sample)`.

### Outputs

Primary output:

- `BatchSummary`

Current summary fields:

- `runs`
- `avgSolutionLength`
- `avgDeadEnds`
- `avgJunctions`
- `avgStraightness`
- `avgCoverage`
- `minSolutionLength`
- `maxSolutionLength`

Side effects:

- One Cortex sample per run when a sink is provided.
- Each generated episode is disposed after measurement.

Current failure modes:

- `runs <= 0` produces invalid averages and extreme min or max placeholders because the function does not guard zero or negative runs.
- Invalid dimensions are not explicitly validated before they reach `buildMaze()`.
- Any `buildMaze()` failure aborts the batch.

### Public Surface

Public function:

- `runBatch(runs, width, height, braidRatio, cortex?): BatchSummary`

Public type:

- `BatchSummary`

Indirect exported support surface:

- `CortexSink`
- `CortexSample`

### Fixtures And Tests

Sample verification path:

- `repos/fawxzzy-mazer/tests/maze/maze-domain.test.ts`

Current tests:

- The domain suite runs `runBatch(12, 50, 50, 0.08, cortex)` and asserts bounded summary metrics plus one emitted sample per run.
- The same suite verifies deterministic generator surfaces that the batch harness depends on.

Expected outputs:

- `runs === 12`
- `avgSolutionLength > 20`
- `avgCoverage` remains within `(0, 1]`
- `maxSolutionLength >= minSolutionLength`
- One pushed sample per run when a sink is provided.

Missing tests:

- No dedicated batch contract file exists.
- No explicit test covers `runs = 0` or invalid dimension inputs.
- No isolated test proves disposal happens for every iteration.

### Dependencies

Runtime dependencies:

- TypeScript and Vitest toolchain in `fawxzzy-mazer`

File dependencies:

- `src/domain/maze/batch.ts`
- `src/domain/maze/generator.ts`
- `src/domain/maze/core.ts`
- `src/domain/maze/types.ts`

Implicit behavioral dependencies:

- `buildMaze()`
- `toCortexSample()`
- `disposeMazeEpisode()`

### Gaps

- `runBatch()` still depends on the larger generator and core helper surfaces.
- Verification still lives in the shared `maze-domain.test.ts` suite rather than a dedicated batch boundary.
- The candidate still lacks explicit zero-run, invalid-dimension, and per-iteration disposal coverage.

### Promotion Target

- Proposed ATLAS module name: `maze-batch`
- ATLAS contract record: `docs/architecture/MAZE-EXTRACTION-CONTRACTS.md`

Minimal refactor needed before promotion:

- Move batch-only assertions into a dedicated contract suite.
- Add input guards for non-positive run counts before extraction is advertised as stable.
- Keep this candidate in Phase 2 until the source boundary and contract tests exist.

### Operational Caveat

- This descendant-validation pass is strong planning evidence, but not a fully trusted nested Codex CLI proof while the local `codex.exe` path still returns `Access is denied`.
- When returning to the CLI verification layer, current Codex docs indicate that project-scoped `.codex/config.toml` only loads for trusted projects, CLI flags override config, and `/sandbox-add-read-dir` is the Windows-native command for temporary sandbox read access.
