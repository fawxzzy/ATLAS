# Pass 2.5 Promotion Notes

What shipped
- A minimal `/settings` App Theme harness for Pass 2 runtime validation.
- Local persistence only.
- No curated onboarding expansion.
- No curated engine work.
- No database-backed theme product.

Why this matters
- Pass 2.5 turns the surface map into a runtime contract instead of a documentation-only claim.

Promotion decision
- Promote the harness itself.
- Do not promote wider theme claims until the protected representative route suite is captured successfully.
- Do not deploy production from runtime theme work until a preview deployment built from the current source passes.

Blocking issue to clear next
- Automated protected-route capture currently redirects to `/login` even when the local capture path provides the stored access token artifact.

Failure mode
- A local visual harness can pass screenshots while production deploy fails if new shared UI files are not tracked or included in the deploy source.

Rule
- Production deploy requires a passing local build and a passing preview deployment after runtime theme changes.

Preview deploy check
- On 2026-04-29, the approved preview-only deploy succeeded from the linked `fawxzzy-fitness` Vercel project and reached `READY`.
- Public preview smoke checks passed for `/login` and `/install`.
- `_stack`'s `fitness:deploy:preflight` still rejects this ATLAS-nested checkout because `repos/fawxzzy-fitness` is not a standalone git toplevel in the current workspace layout.
- Direct repo-linked preview deploy remains viable, but the operator wrapper should be corrected before treating `_stack` preview/prod wrappers as the canonical lane for this checkout.

## 2026-04-29 Current-Session UI Promotion Addendum

What changed
- Current-session live logged-set cards were tightened onto the shared compact-row model instead of keeping one-off inline controls.
- `Warm-Up` now uses the same global yellow `toggleActive` button family as `View`.
- The current-session delete button was resized into a compact pill and moved onto the shared darker destructive family instead of the older lighter red-wash treatment.
- The destructive palette was normalized at the shared primitive layer so delete/discard surfaces that relied on the older lighter style now resolve toward the darker surface plus red text/border treatment.
- Current-session measurement inputs now reuse the floating-border field treatment and horizontal-scroll measurement layout patterns already established elsewhere in the app.

Files that now hold the current product truth
- `repos/fawxzzy-fitness/src/components/SessionTimers.tsx`
- `repos/fawxzzy-fitness/src/components/ui/measurements/MeasurementPanelV2.tsx`
- `repos/fawxzzy-fitness/src/components/ui/MetricItem.tsx`
- `repos/fawxzzy-fitness/src/lib/exercise-goal-format.ts`
- `repos/fawxzzy-fitness/src/app/globals.css`
- `repos/fawxzzy-fitness/src/components/ui/Pill.tsx`
- `repos/fawxzzy-fitness/src/components/ui/app/designSystem.ts`

Next-prod-push posture
- Local repo verification passed with `pnpm run verify`.
- The remaining release risk is not the UI patch itself; it is the fragility of the live capture/dev-server lane on `:3000`.
- Before the next production push, rerun:
  1. a clean local `pnpm run verify`
  2. a clean `qa:dev` boot on `127.0.0.1:3000`
  3. a fresh screenshot proof from the current-session regression route
  4. the existing preview deployment gate from the current workspace source

Operational lesson
- For this repo, "UI looks wrong" and "capture looks wrong" are often different failures.
- Treat stale or misrouted live capture as an environment problem first:
  - confirm the `:3000` listener is the intended fitness server
  - verify `/dev/mobile-regression?scenario=session-logger-strength-weight` returns `200`
  - only then trust screenshots as proof for promotion decisions

## 2026-04-30 Edit-Day / View-Day / Account Addendum

What shipped locally
- View-day header back navigation was restored.
- Edit-day now keeps the list visible and opens an inline single-card dropdown instead of relying on the earlier full-screen feeling branch.
- The expanded edit-day card now uses the attached under-card action strip pattern:
  - left `View`
  - right `Delete`
- Edit-day measurement inputs sit directly under that strip in the shared horizontal measurement rail.
- The old expanded `Order` input is gone.
- Exercise-card goal summaries use the thinner green pipe treatment in both collapsed and expanded states.
- Settings now initialize fully collapsed.
- Legacy migration no longer shows the inline `Not migrated` label.
- The Today header was patched to suppress the extra `Rest day` subtitle.

Files carrying the current truth
- `repos/fawxzzy-fitness/src/app/routines/[id]/days/[dayId]/page.tsx`
- `repos/fawxzzy-fitness/src/app/routines/[id]/edit/day/[dayId]/EditableRoutineDayExerciseList.tsx`
- `repos/fawxzzy-fitness/src/components/session/SessionExerciseBlock.tsx`
- `repos/fawxzzy-fitness/src/components/ui/measurements/MeasurementPanelV2.tsx`
- `repos/fawxzzy-fitness/src/components/ExerciseCard.tsx`
- `repos/fawxzzy-fitness/src/components/ui/app/SignatureSeparator.tsx`
- `repos/fawxzzy-fitness/src/components/workout/ExerciseDisclosureCard.tsx`
- `repos/fawxzzy-fitness/src/app/today/page.tsx`
- `repos/fawxzzy-fitness/src/components/settings/LegacyMigrationSettings.tsx`
- `repos/fawxzzy-fitness/src/components/settings/SettingsAccordionClient.tsx`

Live proof captured from the real signed-in local app
- View day:
  - `tmp/captures/fawxzzy-fitness/view-day-live-window-20260430-0127.png`
- Edit day:
  - `tmp/captures/fawxzzy-fitness/edit-day-live-window-20260430-0129.png`
- Edit day expanded:
  - `tmp/captures/fawxzzy-fitness/edit-day-expanded-live-window-20260430-0130.png`

Capture workflow correction
- Stop spawning many browser windows for one UI pass.
- Preferred workflow is one dedicated Codex-owned signed-in Edge window on `127.0.0.1:3000`, reused across route captures.
- If screenshots and UI disagree, confirm the live route id and the `:3000` owner before changing code.

Next-prod-push posture
- Local verification passed:
  - `npm run test:app-theme`
  - `npm run build`
- Preview-only deploy had already succeeded earlier in this thread on the approved Vercel non-prod project.
- Production still did not ship in this thread.
- These UI changes are suitable to ride the next approved production deployment once the normal prod gate is explicitly reopened.

Remaining caution
- Fresh trustworthy screenshots for the final Today/settings micro-patches were blocked by a local live-route loading stall while compiling `/today`.
- The code is green; the remaining gap is visual proof for those last two screens, not a known build failure.
