# Pass 2.5 Visual Change Workflow

Goal
- Use `/settings` App Theme as the first runtime proof harness for the Pass 2 surface map.

Workflow
1. Open `/settings`.
2. Expand `App Theme`.
3. Apply `Test Theme`.
4. Capture before/after on representative routes.
5. Record each route family as `passed`, `failed`, or `blocked`.
6. Classify misses as:
   - token gap
   - intentional local exception
   - unmapped surface
   - component-specific styling debt

Current local evidence
- Public auth/install family:
  - Passed with screenshot evidence in `tmp/pass-2-5-screenshots/`
- Protected app family:
  - Blocked by auth redirect during automated capture

Rule
- Theme controls must mutate semantic UI groups, not individual route-local components.

Failure mode
- If a setting only changes the current screen, the harness is not validating the surface graph.

Failure mode
- If protected routes cannot be entered during capture, do not mark the family as passed from code inspection alone.

## 2026-04-29 Live Workflow Addendum

Observed live-workflow failures
- The same route alternated between `200`, `404`, and `500` depending on whether the real fitness dev server was actually the process bound to `127.0.0.1:3000`.
- Screenshot framing scripts could produce misleading proof when they scrolled to the wrong region or reused a flow built for a prior request.
- Switching a local in-card control onto a shared global button family can expose real layout incompatibilities immediately; the screenshot failure was useful because it revealed that the first warm-up control swap was structurally wrong for that slot.

Reliable recovery sequence used in this pass
1. confirm the intended route directly:
   - `http://127.0.0.1:3000/dev/mobile-regression?scenario=session-logger-strength-weight`
2. if the route is `404`, `500`, or missing expected UI text:
   - stop the listener on `:3000`
   - run `pnpm run clean:next` in `repos/fawxzzy-fitness`
   - start one server only with `pnpm run qa:dev`
3. poll the route until it returns `200`
4. use a fresh screenshot filename for every recapture
5. inspect the generated image before showing it to the user

Rule
- Do not treat a live screenshot as authoritative until the route status, server identity, and captured frame have all been checked.
