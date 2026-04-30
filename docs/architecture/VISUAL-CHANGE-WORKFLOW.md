# Pass 2.5 Visual Change Workflow

Goal
- Turn the screen/surface map into an executable validation loop instead of relying on memory-driven screenshot checks.

Hard rule
- AI live UI work must use a Codex-owned isolated browser profile only.
- Do not use the user's personal browser windows, active logged-in browser, or random spawned user-facing windows.

Workflow
1. Predict affected routes and surfaces from the token map.
2. Apply the code change.
3. Run local verification:
   - `npm run test:app-theme`
   - `npm run build`
4. Start the intended app server.
5. Confirm the intended route returns the expected page.
6. Capture screenshots in a Codex-owned browser context.
7. Compare expected vs actual surface mutations.
8. Record each route family as `passed`, `failed`, or `blocked`.
9. Patch and repeat until the changed family is explained.

Capture contract
- Every live capture should identify:
  - app
  - base URL
  - route
  - viewport
  - auth state
  - setup action
  - expected surface family
  - screenshot output path

Classification rules for misses
- token gap
- intentional local exception
- unmapped surface
- component-specific styling debt
- invalid capture environment

Reliable recovery sequence
1. Confirm the intended route directly on `127.0.0.1:3000`.
2. If the route is `404`, `500`, or missing expected UI text:
   - stop the existing listener on `:3000`
   - clear stale local build state if needed
   - start one server only
3. Poll until the route returns `200`.
4. Use a fresh screenshot filename for every recapture.
5. Inspect the resulting image before treating it as evidence.

Failure modes
- Using the user's browser creates privacy risk, session confusion, stale state, and unreliable screenshots.
- Single screenshot edits without route/state expectation recreate the human-memory bottleneck.
- A green screenshot on the wrong route or wrong server is invalid proof.

Promotion posture
- Preview deploy only while Pass 2.5 App Theme work is active.
- Production remains gated until the representative protected route suite is visually proven in a Codex-owned browser.

Related docs
- `docs/architecture/THEME-MUTATION-TEST-PLAN.md`
- `docs/architecture/DESIGN-SURFACE-TOKEN-MAP.md`
- `docs/architecture/COMPONENT-STYLING-COVERAGE.md`
- `docs/architecture/ATLAS-VISUAL-OPERATOR.md`
