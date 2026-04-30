# Pass 2.5 Theme Mutation Test Plan

Status
- Implemented in `repos/fawxzzy-fitness` as a local-only `/settings` App Theme harness.
- Stored in `localStorage` under `fawxzzy:app-theme`.
- Applied at the document root through `AppThemeBootstrap`.
- Current lane: Pass 2.5 App Theme V1.1 semantic-lane coverage, preview only, production still gated.

Harness controls
- Theme preset: `Default`, `Test Theme`
- Primary action
- Secondary action
- Accent / Divider
- Surface / Card
- Success / Complete
- Warning
- Button radius
- Card radius
- Advanced:
  - Selection / Active
  - Loader / Scan
- Reset theme

Semantic variables exercised
- Primary action:
  - `--accent`
  - `--accent-strong`
  - `--accent-mint`
  - `--accent-blue`
  - `--accent-purple`
- Secondary action:
  - `--secondary-action-rgb`
- Accent / Divider:
  - `--accent-divider-rgb`
- Success / Complete:
  - `--success-rgb`
- Selection / Active:
  - `--selection-rgb`
- Loader / Scan:
  - `--loader-scan-rgb`
- Warning:
  - `--warning-rgb`
  - `--accent-yellow-off`
  - `--accent-yellow-on`
- Surface / Card:
  - `--surface-1-rgb`
  - `--surface-2-rgb`
  - `--surface-3-rgb`
  - `--bg-panel`
  - `--bg-card`
  - `--bg-shell`
  - `--glass-tint-rgb`
- Button radius:
  - `--button-radius`
  - `--bottom-action-radius`
  - `--action-chrome-shell-radius`
  - `--action-chrome-segment-radius`
  - `--action-chrome-segment-radius-compact`
- Card radius:
  - `--card-radius`
  - `--radius-sm`
  - `--radius-md`
  - `--radius-lg`
  - `--radius-xl`

Targeted V1.1 surface families
- Secondary action:
  - yellow/default secondary dock actions
  - secondary action chrome
- Accent / Divider:
  - signature pipes
  - thin card dividers
  - history separator bars
  - weekday accent text
  - thin green strips and metadata dots
- Success / Complete:
  - completed-card text
  - completed exercise rows
  - completed session disclosure shells
- Selection / Active:
  - selected exercise rows
  - selected picker pills
  - today/active badges
- Loader / Scan:
  - route loading scan/glow
- Warning:
  - rest-day and warning chips/cards

Required validation flow
1. Apply `Test Theme` from `/settings`.
2. Run `npm run test:app-theme`.
3. Run `npm run build`.
4. Capture representative route evidence with a Codex-owned isolated browser only.
5. Mark each route family as `passed`, `failed`, or `blocked`.
6. Preview deploy only after local verification is green.

Representative route suite
- Public:
  - `/login`
  - `/install`
- Protected:
  - `/settings`
  - `/today`
  - `/routines`
  - `/routines/[id]/edit/day/[dayId]`
  - `/session/[id]`
  - `/history`
  - `/history/exercises`
  - add-exercise flows

Operator rule
- AI live UI work must use a Codex-owned browser context only.
- Do not use the user's personal browser, active logged-in browser, or random user-facing windows for capture or interaction.

Evidence posture
- Public-route screenshot proof exists under `tmp/`.
- Protected-route proof must be refreshed after the semantic-lane expansion because `/session/[id]`, edit-day, today, and history surfaces changed materially.
- Do not mark the V1.1 lane complete from code inspection alone.

Known risks
- Some generated design-system classes still embed fixed radii and remain partial radius debt.
- Protected-route capture is still more fragile than the token layer itself because it depends on valid auth artifacts and the correct local server owning `127.0.0.1:3000`.
- Preview can be green while production remains intentionally gated.

Promotion gate
- Do not deploy production from App Theme work in this pass.
- Promotion remains blocked on:
  - passing `npm run test:app-theme`
  - passing `npm run build`
  - fresh Codex-owned visual proof for the representative protected route suite
  - a preview deployment sourced from the current workspace
