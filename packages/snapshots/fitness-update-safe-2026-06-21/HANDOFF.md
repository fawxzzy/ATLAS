# Fitness Update-Safe Handoff

Date: 2026-06-21
Workspace root: `ATLAS root`
Implementation repo: `repos/fawxzzy-fitness`
Git branch: `main`
Git head: `75e29aef`

## Purpose

This file is a durable local handoff so the Codex desktop app can be updated without depending on the current live thread context.

## Current resume point

Resume work on the add-exercise screen in:

- `repos/fawxzzy-fitness/src/components/ExercisePicker.tsx`
- `repos/fawxzzy-fitness/src/components/ui/app/SignatureSeparator.tsx`

The active workstream is custom-exercise draft logic and visual polish on the add-exercise surface.

## Latest completed work

1. Custom selected exercise draft card now shows `Current Target` in the same header-side companion pattern as selected exercise cards.
2. Current-target requirement logic was corrected so combined signals resolve more intentionally:
   - movement and equipment override when they imply a stronger modality
   - muscle-only fallback now uses local exercise-library evidence
   - hidden stale selected tags are now surfaced in submenu trays so they can be cleared
3. Verified live that:
   - stale `Stretch` / `Bodyweight` / other latent selections can now be surfaced and cleared
   - a pure primary-muscle-only `Back` case resolves to `Needs reps`, not `Needs time`
4. Shared pipe separator was normalized in `SignatureSeparator.tsx` to self-center instead of riding baseline alignment.

## Important behavior notes

### Custom requirement inference

The custom draft requirement logic now follows this shape:

- `stretch` / `mobility` / recovery-style movement -> `time`
- `carry` -> `distance`
- cardio-like movement or equipment such as `gait`, `treadmill`, `bike`, `rower`, `erg`, `elliptical`, `stair`, `ski` -> `time`
- otherwise muscle-only drafts fall back to dominant evidence from the local exercise library

### Hidden tag bug that was fixed

Previously, seeded or legacy custom selections could remain active even when they were not shown inside the current submenu options. That caused confusing requirement text such as `Needs time` while the visible selection looked like a strength-only profile.

That bug was addressed by ensuring currently selected submenu tags are injected back into the visible group list so they can always be seen and cleared.

## Latest visual QA references

These local screenshots were generated during verification:

- `custom-back-only-final.png`
- `custom-back-after-fix.png`
- `pipes-centered-check.png`

## Latest user concern

The most recent user concern before update:

> the pipes in the cards are sitting a little high not vertically ceneter mass aligned.. this is a huge common issue we run into with ui elemnts in general like helllllaaaaaaaaaaaaaaa

That concern was addressed by changing the shared `SignatureMiniPipe` primitive rather than nudging one screen only.

## Verification status

Confirmed in this session:

- `npm run typecheck` passed after the latest edits
- live browser verification was run against:
  - `http://127.0.0.1:3002/dev/mobile-regression?screen=add-exercise&fixture=custom-taxonomy`

## Next best resume actions

If work resumes after the app update, the next highest-value checks are:

1. Re-open the add-exercise custom taxonomy fixture and confirm the shared pipe centering looks correct across:
   - selected custom card metadata row
   - title/target separator
   - normal exercise card metadata rows
2. If any pipe still rides high, audit the caller row for mixed line-height or `items-start` layout before changing the shared primitive again.
3. Continue the add-exercise polish pass from this same surface rather than switching screens.

## Safety note

Repo progress is on disk. The only thing this handoff is protecting against is losing live chat context during the Codex desktop app update/restart.
