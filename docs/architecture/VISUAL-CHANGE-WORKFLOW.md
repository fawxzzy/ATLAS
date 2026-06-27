# Pass 2.5 Visual Change Workflow

Goal
- Turn the screen/surface map into an executable validation loop instead of relying on memory-driven screenshot checks.

Hard rule
- AI live UI work must use a Codex-owned isolated browser profile only.
- Do not use the user's personal browser windows, active logged-in browser, or random spawned user-facing windows.

Workflow
1. Predict affected routes and surfaces from the token map.
2. Identify the canonical surface or component when the request implies cross-screen normalization.
3. Convert the requested visual edits into an explicit checklist before mutating code.
4. Apply the code change.
5. Run local verification:
   - `npm run test:app-theme`
   - `npm run build`
6. Start the intended app server.
7. Confirm the intended route returns the expected page.
8. Capture screenshots in a Codex-owned browser context.
9. Compare expected vs actual surface mutations.
10. Reconcile the requested-edit checklist item-by-item as `passed`, `failed`, `blocked`, or `deferred`.
11. Record each route family as `passed`, `failed`, or `blocked`.
12. Patch and repeat until the changed family is explained.

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
  - canonical surface under test when normalization is in scope
  - requested-edit checklist id or note
  - data lane: `qa_fixture`, `automation_user`, or `live_user_bounded`

Mobile-first rule
- For mobile-first Fitness surfaces, proof should include at least one mobile lens in addition to desktop sanity.
- Desktop-only captures may support debugging, but they should not be treated as full UI-closeout proof for mobile-first work.

Current Fitness execution
- Verified repo-local command:
  - `npm run visual:fitness:theme`
- Verified isolated profile run on April 29, 2026 wrote evidence to:
  - `tmp/captures/fitness/visual-operator/theme/2026-04-29`
- Final proof follow-up run on April 29, 2026 wrote evidence to:
  - `tmp/captures/fitness/app-theme-v1_1-final-proof/2026-04-29-preview`
- Screenshot-backed protected route proof now exists for:
  - `/settings`
  - `/today`
  - `/routines`
  - `/session/[id]`
  - `/session/[id]/add-exercise`
  - `/routines/[id]/edit/day/[dayId]`
  - `/routines/[id]/edit/day/[dayId]/add-exercise`
  - `/history`
  - `/history?view=detailed`
  - `/history/[sessionId]`
  - `/history/exercises` compact
  - `/history/exercises` detailed
- Separate closeout evidence also exists under:
  - `tmp/captures/fitness/app-theme-v1_1-closeout/2026-04-29`
- Use the closeout set for:
  - settings panel-open proof
  - loader/scan proof
  - the ad hoc `edit-day-expanded` delta image
- Use the final-proof preview set for:
  - canonical preview `/login` smoke
  - canonical preview `/install` smoke
  - documented proof that the available isolated auth artifact still redirects preview `/settings` to `/login`

Classification rules for misses
- token gap
- intentional local exception
- unmapped surface
- component-specific styling debt
- invalid capture environment
- requested edit not landed
- canonical surface mismatch

Reliable recovery sequence
1. Confirm the intended route directly on `127.0.0.1:3000`.
2. If the route is `404`, `500`, or missing expected UI text:
   - stop the existing listener on `:3000`
   - clear stale local build state if needed
   - start one server only
3. Poll until the route returns `200`.
4. Use a fresh screenshot filename for every recapture.
5. Inspect the resulting image before treating it as evidence.

Mutable data rule
- Prefer QA fixtures or automation-user data for visual work that requires product mutations.
- If live user data is touched during investigation, record the targeted records first and restore or explicitly report any residual changes before closeout.

Failure modes
- Using the user's browser creates privacy risk, session confusion, stale state, and unreliable screenshots.
- Single screenshot edits without route/state expectation recreate the human-memory bottleneck.
- A green screenshot on the wrong route or wrong server is invalid proof.
- A preview build can be READY while isolated protected auth is still unavailable and the local `:3000` lane is too stalled to produce fresh trustworthy proof.
- Patching sibling routes independently instead of normalizing from the canonical surface creates repeating drift and false `fixed` states.
- Passing tests with no requested-edit reconciliation can still leave the actual UI batch partially unfinished.

Promotion posture
- Preview deploy only while Pass 2.5 App Theme work is active.
- Production remains gated until the representative protected route suite is visually proven in a Codex-owned browser.
- Protected/history proof is no longer blocked in the verified local isolated profile.
- Loader/scan and settings-panel-open still remain closeout-only proof in the final proof pass.
- Production still remains gated in this thread because preview-green is not the same as promotion approval.

Related docs
- `docs/architecture/THEME-MUTATION-TEST-PLAN.md`
- `docs/architecture/DESIGN-SURFACE-TOKEN-MAP.md`
- `docs/architecture/COMPONENT-STYLING-COVERAGE.md`
- `docs/architecture/ATLAS-VISUAL-OPERATOR.md`
