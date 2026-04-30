# Atlas Visual Operator

Purpose
- Provide a reusable stack-level operator for live-app screenshot capture, visual validation, and patch iteration.
- Start with Fitness Pass 2.5, but keep the contract app-agnostic.

Operator rule
- AI live UI work must use a Codex-owned browser only.
- Use an isolated profile directory per app or app/environment pair.
- Do not use the user's personal browser windows or active logged-in browser as the automation surface.

Core contract
- Every capture job should define:
  - `app`
  - `baseUrl`
  - `route`
  - `viewport`
  - `authState`
  - `setupAction`
  - `expectedSurfaceFamily`
  - `outputPath`

Expected execution loop
1. predict affected surfaces from the surface map
2. apply code change
3. run local tests/build
4. boot the intended app server
5. confirm the route/state is valid
6. capture screenshot(s) in the Codex-owned browser
7. compare expected vs actual mutations
8. record misses
9. patch and repeat

Browser ownership model
- one reusable signed-in session per app/environment
- one isolated profile directory per session family
- one controlled viewport per capture target
- one evidence path under `tmp/` for disposable artifacts

Fitness integration points
- Current source-of-truth docs:
  - `docs/architecture/THEME-MUTATION-TEST-PLAN.md`
  - `docs/architecture/DESIGN-SURFACE-TOKEN-MAP.md`
  - `docs/architecture/COMPONENT-STYLING-COVERAGE.md`
  - `docs/architecture/VISUAL-CHANGE-WORKFLOW.md`
- Future evidence ledger integration when those files exist:
  - `SCREEN-DELTA-LEDGER.md`
  - `SCREEN-SURFACE-VARIANT-LEDGER.md`
  - `SURFACE-SIMILARITY-GRAPH.md`

Minimal first command
- Preferred first public contract:
  - `atlas visual capture --app fitness --suite theme`
- Acceptable repo-local bootstrap while the Atlas wrapper is still documentation-only:
  - `npm run visual:fitness:theme`

Failure modes
- user browser reuse creates privacy and session-risk
- stale `:3000` listener gives false screenshot evidence
- route/state mismatch makes a correct screenshot useless
- one-off screenshots without a surface-family expectation recreate manual review drift

Scope boundary
- This document defines the operator contract and rules.
- It does not require broad new automation in this pass.
- Implement only the minimal first command once the contract is stable and the Fitness route/state suite is clean.
