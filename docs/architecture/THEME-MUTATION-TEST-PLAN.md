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
