# Fawxzzy Fitness Live UI Handoff

Date:
- 2026-04-30

Workspace:
- `repos/fawxzzy-fitness`

Scope covered in this thread:
- approved Vercel preview-only link and deploy
- preview verification and protected-route capture debugging
- live mobile UI refinement for:
  - view day
  - edit day
  - edit-day expanded exercise dropdown
  - account/settings
  - today header cleanup
- screenshot workflow recovery for real signed-in local captures

## Deployment state

Preview-only deploy was completed against the approved project:
- project: `fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- team id: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- preview URL:
  - `https://fawxzzy-fitness-ltli2e5of-fawxzzy.vercel.app`

Verified during the deploy pass:
- `npm run test:app-theme` passed
- `npm run build` passed
- preview reached `READY`
- public preview smoke checks passed for:
  - `/login`
  - `/install`

Production was not deployed in this thread.

## Final live UI state from this thread

### View day

Confirmed live route:
- `http://127.0.0.1:3000/routines/c050c096-bb4a-42a7-a0bf-d50c8742d787/days/ebb2ac9e-16b1-4490-b5ef-2d51aa974d04`

Confirmed screenshot:
- `tmp/captures/fawxzzy-fitness/view-day-live-window-20260430-0127.png`

Intended state:
- header back button restored
- back target returns toward the base routine flow instead of stranding the user in the day screen

Primary file:
- `repos/fawxzzy-fitness/src/app/routines/[id]/days/[dayId]/page.tsx`

### Edit day

Confirmed live route:
- `http://127.0.0.1:3000/routines/c050c096-bb4a-42a7-a0bf-d50c8742d787/edit/day/ebb2ac9e-16b1-4490-b5ef-2d51aa974d04`

Confirmed screenshots:
- default:
  - `tmp/captures/fawxzzy-fitness/edit-day-live-window-20260430-0129.png`
- expanded:
  - `tmp/captures/fawxzzy-fitness/edit-day-expanded-live-window-20260430-0130.png`

Current intended behavior:
- bottom dock on the normal edit-day screen remains:
  - left `Reorder`
  - right `Add`
- tapping an exercise opens an inline dropdown instead of navigating to a separate full-screen editor
- only one inline dropdown can be open at once
- expanded card keeps the full list visible
- expanded card uses an attached under-card action strip:
  - left `View`
  - right `Delete`
- the under-card strip reuses the same attached sharp-edge design family used by the logged-session card lane
- measurement inputs render directly under that strip in the horizontal scroll rail
- the old expanded `Order` field is removed
- the summary line uses `Set # | ...` with the thinner green pipe treatment
- the exercise-card chevron follows the dropdown pattern for this screen
- the opened card uses the sharper lower edge so it sits flush with the attached strip

Primary files:
- `repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/EditableRoutineDayExerciseList.tsx`
- `repos/fawxzzy-fitness/src/components/session/SessionExerciseBlock.tsx`
- `repos/fawxzzy-fitness/src/components/ui/measurements/MeasurementPanelV2.tsx`
- `repos/fawxzzy-fitness/src/components/ExerciseCard.tsx`
- `repos/fawxzzy-fitness/src/components/ui/app/SignatureSeparator.tsx`
- `repos/fawxzzy-fitness/src/components/workout/ExerciseDisclosureCard.tsx`

## Today and settings follow-up changes

These code changes landed after the edit-day pass:
- remove the extra `Rest day` subtitle from the Today header
- stop showing the inline `Not migrated` status copy in the legacy migration section
- initialize settings/account accordion sections collapsed instead of opening `Data & Account` by default

Primary files:
- `repos/fawxzzy-fitness/src/app/today/page.tsx`
- `repos/fawxzzy-fitness/src/components/settings/LegacyMigrationSettings.tsx`
- `repos/fawxzzy-fitness/src/components/settings/SettingsAccordionClient.tsx`

Verification for this pass:
- `npm run test:app-theme`
- `npm run build`

Known limitation at handoff time:
- after the final Today/settings patch, the local signed-in browser lane stalled while compiling `/today`
- fresh trustworthy screenshots were captured for:
  - view day
  - edit day
  - edit day expanded
- fresh trustworthy screenshots were not captured for:
  - today after the header cleanup
  - settings after the collapsed-default / migration-label cleanup
- the code changes are in and the full build is green, but visual proof for those last two screens still needs a stable live capture run

## Browser capture workflow that should replace the earlier many-window churn

Preferred rule:
- use one dedicated Codex-owned browser window or tab group only
- reuse that same signed-in window for route-to-route captures instead of spawning a new window for every screen

What actually mattered in this thread:
- saved login/autofill was keyed to `127.0.0.1:3000`, not `3001`
- the live screenshot lane became reliable only after restoring the fitness dev server on `127.0.0.1:3000`
- stale auth artifacts and copied headless profile lanes were less reliable than the real signed-in Edge profile

Recommended capture order next time:
1. make sure one healthy server owns `127.0.0.1:3000`
2. open one dedicated Edge window on the signed-in default profile
3. start from `/routines`
4. navigate to the exact live route needed
5. capture to a fresh filename every time
6. avoid the regression route for protected-screen truth unless auth is broken and only local layout proof is needed

Known stable live route IDs at the end of this thread:
- routine id:
  - `c050c096-bb4a-42a7-a0bf-d50c8742d787`
- day id:
  - `ebb2ac9e-16b1-4490-b5ef-2d51aa974d04`

## High-signal summary for the next ChatGPT handoff

What is done:
- preview-only Vercel link and deploy succeeded on the approved non-prod project
- local `app-theme` checks and local build passed
- view-day back button is back
- edit-day uses the inline single-card dropdown model with attached `View/Delete` strip and horizontal measurement rail
- the heavy green pipe issue on exercise-card summaries was corrected in the shared renderer
- settings now opens collapsed
- legacy migration no longer shows the inline `Not migrated` note
- today header no longer intends to show the extra `Rest day` subtitle

What still needs caution:
- production was not deployed in this thread
- protected-route screenshot proof is reliable again for view/edit day, but the Today/settings lane stalled during the final capture attempt
- do not treat stale or half-loaded screenshots as UI truth without confirming the `:3000` runtime and route load state first

What should ride the next approved prod deployment:
- the edit-day/view-day/account/today code changes from this thread
- only after the normal prod gate is explicitly reopened

## Continued live loop updates after the initial handoff

This thread continued past the first handoff and added both UI changes and important local-runtime findings.

### Additional UI changes landed in the same local loop

Login and shared accent changes:
- narrowed the shared green pipe horizontally without changing its height
- reduced the shared green accent dot size slightly across the app
- added a subtle green outline/glow treatment to the main white login title copy

Today screen:
- replaced white bullet separators in the Today subtitle treatment with the shared green accent dot
- reduced that Today subtitle dot to a smaller override size than the default shared dot

PWA / install surface:
- manifest install naming now uses `FawxzzyFitness`
- added Apple touch icon aliases so iOS install flows stop probing missing assets
- dev service-worker bootstrap no longer forces a reload cycle while cleaning up dev caches

Loading shell:
- route-loading states now temporarily suppress the thin app edge frame during boot / load surfaces

App Theme mobile edits:
- save slots now read:
  - `Default`
  - `Slot 1`
  - `Slot 2`
  - `Slot 3`
- removed the old `Saved themes` title
- centered the theme-name input more cleanly
- widened the inner grouped mobile shells horizontally
- hid the larger grouped shell borders
- inserted centered horizontal green separator bars between the larger theme groups
- removed visible hex readout text from the color inputs while preserving the actual color controls
- shortened `Success / Complete` to `Success`

Primary files touched during the continued pass:
- `repos/fawxzzy-fitness/src/components/ui/app/SignatureSeparator.tsx`
- `repos/fawxzzy-fitness/src/app/today/page.tsx`
- `repos/fawxzzy-fitness/src/app/today/TodayDayPicker.tsx`
- `repos/fawxzzy-fitness/src/app/manifest.ts`
- `repos/fawxzzy-fitness/src/components/ServiceWorkerBootstrap.tsx`
- `repos/fawxzzy-fitness/src/components/ui/app/designSystem.ts`
- `repos/fawxzzy-fitness/src/components/RouteLoading.tsx`
- `repos/fawxzzy-fitness/src/app/globals.css`
- `repos/fawxzzy-fitness/src/components/settings/AppThemeSettings.tsx`

## Data-source and auth findings

The local app was not initially reading from the same Supabase project as production.

What was discovered:
- one local lane was using:
  - `https://hcjbdxrekkbfbngrfvcv.supabase.co`
- the production-aligned QA session and the desired Atlas routine data lived under:
  - `https://lpswxoyfniocuhljgzbc.supabase.co`

What was changed:
- a repo-local `.env.local` was added in `repos/fawxzzy-fitness` to pin local public Supabase credentials to the production-aligned project

Operational consequence:
- aligning the data source does not automatically align the signed-in member account
- if the user still sees the old `4Dayz` routine after env alignment, the local browser or phone is authenticated as the wrong user for that data set

## Mobile / PWA dev findings that should not be rediscovered next time

### Home Screen PWA is a bad truth surface for `next dev`

Main finding:
- iPhone Home Screen standalone mode is not a reliable live-preview target for this repo while running `next dev`

Why:
- iOS aggressively caches manifest, icons, launch metadata, and installed shell state
- standalone mode can hold stale route shells and stale chunk maps longer than Safari
- Next Fast Refresh and full-reload events can leave the installed shell asking for dead chunk paths during active local edits

Practical rule for future local loops:
- use desktop as the primary live preview
- use iPhone Safari for device checks during local development
- avoid treating the installed Home Screen app as the source of truth during local dev iteration
- if manifest naming or install assets change, remove the old Home Screen install and add it again

### The mobile `404 after login` was a runtime split-brain issue

The main mobile failure was not a product-data problem. It was a bad local server state.

What actually happened:
- desktop was able to work because one healthy Node process owned `127.0.0.1:3000`
- phone traffic was hitting a different stale Node process on `0.0.0.0:3000`
- this created a split-brain local runtime where desktop and phone were not talking to the same dev server

Evidence captured during the session:
- `netstat` showed simultaneous listeners on:
  - `0.0.0.0:3000`
  - `127.0.0.1:3000`
- the phone-visible LAN route returned real route failures while loopback stayed healthy
- specifically, `http://192.168.12.156:3000/entry` returned `404` during the broken state even while desktop login and other loopback checks were healthy

Additional stale-runtime symptoms captured in logs:
- stale chunk requests after auth redirects
- `MODULE_NOT_FOUND` inside `.next/server/webpack-runtime.js`
- missing generated chunk files such as `./1682.js`
- `TypeError: __webpack_modules__[moduleId] is not a function`
- intermittent route `404` and `500` responses caused by corrupted / stale `.next` output under the wrong process mix

### Correct recovery procedure

The reliable recovery sequence for this repo is:
1. kill all stale repo-owned Node listeners on the target dev port
2. verify only `TIME_WAIT` remains and there is no active `LISTENING` owner left on the port
3. clean `.next`
4. relaunch one single LAN-bound dev server
5. verify both loopback and LAN against the same process before using the phone again

The repo-owned launcher that eventually recovered the loop was:
- `npm run qa:dev:fresh -- --hostname 0.0.0.0 --port 3000 --clean-next true`

Important caution:
- if stale listeners still own `3000`, the fresh launcher can fail with `EADDRINUSE` and give misleading route-health results until the old processes are forcibly stopped

### Current known-good local posture at the end of the session

Known-good behavior after cleanup:
- one single listener on `0.0.0.0:3000`
- desktop:
  - `http://127.0.0.1:3000`
- phone:
  - `http://192.168.12.156:3000`
- route checks that were healthy after the cleanup:
  - `/login`
  - `/today`
  - `/entry`

## Recommended continuation rules for the next operator

- keep the local loop on `3000` unless there is a specific reason to move
- treat `runtime/receipts/dev/dev-server.latest.json` as the first truth source for the currently managed dev instance
- if phone and desktop disagree, assume split-brain runtime or stale installed-shell cache before assuming the code change broke app logic
- prefer Safari over the Home Screen install for active local device verification
- if the phone route breaks after login again, check whether `/entry` differs between `127.0.0.1:3000` and `192.168.12.156:3000` before touching application code
