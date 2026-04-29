# Pass 2.5 Theme Mutation Test Plan

Status
- Implemented in `repos/fawxzzy-fitness` as a local-only `/settings` App Theme harness.
- Stored in `localStorage` under `fawxzzy:app-theme`.
- Applies at the document root through `AppThemeBootstrap`.

Harness controls
- Theme preset: `Default`, `Test Theme`
- Primary action color
- Surface/card color
- Button radius
- Card radius
- Reset theme

Semantic variables exercised
- Primary action: `--accent`, `--accent-strong`, `--accent-mint`, `--accent-blue`, `--accent-purple`
- Surface/card: `--surface-1-rgb`, `--surface-2-rgb`, `--surface-3-rgb`, `--bg-panel`, `--bg-card`, `--bg-shell`, `--glass-tint-rgb`
- Button radius: `--button-radius`, `--bottom-action-radius`, `--action-chrome-shell-radius`, `--action-chrome-segment-radius`, `--action-chrome-segment-radius-compact`
- Card radius: `--card-radius`, `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`

Evidence
- Public before/after screenshots were captured locally at:
  - `tmp/pass-2-5-screenshots/login-before.png`
  - `tmp/pass-2-5-screenshots/login-after.png`
  - `tmp/pass-2-5-screenshots/install-before.png`
  - `tmp/pass-2-5-screenshots/install-after.png`
- Protected-route capture is currently blocked.
  - Direct request evidence shows `/settings` still redirects to `/login` even when `x-atlas-access-token` is provided from `runtime/fitness/live-user-auth-current-project.json`.

Observed results
- Primary action color:
  - Passed on `/login` bottom action (`Enter Gym`)
  - Passed on `/install` positive dock action (`Go to login`)
- Surface/card color:
  - Passed on `/login` auth card
  - Passed on `/install` install card
- Radius:
  - Passed visibly on public auth/install shells after exaggerating `Test Theme`
  - Still only partially bridged across the wider app because some compiled design-system classes retain fixed radius literals

Current blockers
- Local `npm run build` now passes in `repos/fawxzzy-fitness`, so the current production red state is not reproduced by the checked-out workspace itself.
- The dedicated theme harness test must run through the repo alias loader.
  - Direct `node --test src/lib/app-theme.test.ts` fails with `ERR_MODULE_NOT_FOUND` for `@/lib/app-theme`.
  - The repeatable command is `npm run test:app-theme`.
- Production deploy health can still fail independently of the local visual harness when deploy source and workspace source drift.
  - Current failure mode: `src/components/ui/LabeledEditorField.tsx` exists locally but the failing production deploy did not resolve `@/components/ui/LabeledEditorField`.
- Protected-route capture remains blocked in this workspace until a fresh QA session artifact can be minted from valid local QA credentials.
  - `runtime/fitness/qa-session.json` exists, but the stored session is stale and `npm run qa:session` cannot refresh it here without `FITNESS_QA_EMAIL` / `FITNESS_QA_PASSWORD`.

Blocked route set
- The representative protected validation set remains blocked until capture auth is repaired:
  - `/settings`
  - `/today`
  - `/routines`
  - `/routines/[id]/edit/day/[dayId]`
  - `/session/[id]`
  - `/history`
  - `/history/exercises`

Next patch list
- Repair protected-route capture auth so the representative suite can be re-run.
- Promote remaining fixed-radius primitives to semantic variables where they are supposed to follow the card lane.
- Re-run before/after captures for the blocked protected routes with the existing `Test Theme`.
- Keep production gated on:
  - a passing local build
  - a passing `npm run test:app-theme`
  - a successful preview deployment sourced from the current workspace changes

## 2026-04-29 Destructive-Lane Note

Additional semantic lane proved during the current-session pass
- Destructive controls are effectively their own shared visual lane and must be treated as a global family, not as isolated red local overrides.

Confirmed shared destructive surfaces updated in the repo
- `bottom-action` danger buttons already used the darker dark-surface plus red-text treatment.
- `action-chrome` danger buttons were lighter and were realigned to the darker family.
- destructive badge/pill primitives were also realigned so delete/discard chips stop diverging from button treatment.

Current lesson
- When the user asks for "make this delete/discard look like the other delete/discard buttons," inspect the shared primitive path first:
  - `bottom-action` danger
  - `action-chrome` danger
  - destructive badge/pill tokens
- If those lanes disagree, fix the shared token family before adding more per-screen overrides.
