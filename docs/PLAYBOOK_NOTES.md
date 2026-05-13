# Playbook Notes

## 2026-05-11 - QA LLEL adoption semantics

- Rule: repo blockers exposed by QA LLEL should be fixed in the owning repo, not hidden in root QA logic.
- Rule: package and docs repos should not report browser-emulation semantics unless browser evidence actually exists.
- Rule: a failed preflight must block promotion for every evidence profile, including docs governance.
- Rule: repo lint failures are repo-owned blockers; root QA should surface them, not bypass them.
- Pattern: root-owned capture machinery should also own its runtime dependencies; child repos should declare only app or command intent.
- Pattern: adoption means child-owned QA intent plus root-readable receipts, not root-side prototype manifests.
- Pattern: warning counts should become a governed budget before they become promotion blockers.
- Pattern: visual diff failures must be classified before either UI remediation or baseline blessing.
- Failure Mode: blessing a baseline before classifying the diff turns QA into approval theater.
- Failure Mode: letting non-visual repos report as browser-emulation passes creates semantic drift unless the evidence profile is shown separately from the promotion outcome.
- Failure Mode: treating hundreds of warnings as harmless creates silent governance debt.
- Failure Mode: fixing repo failures in root QA logic hides ownership and weakens the evidence model.

## 2026-04-28 - Fitness live UI and real mobile screenshot lane

- Rule: for live mobile UI refinement on fitness, prefer the real signed-in local app on `http://127.0.0.1:3000` and use isolated browser sessions only.
- Rule: keep the user's personal browser windows untouched; launch and close Codex-owned browser sessions only.
- Rule: store durable runtime auth in `runtime/fitness/live-user-auth-current-project.json` and refresh it before capture work instead of creating throwaway users.
- Rule: keep screenshot artifacts in repo-local `.codex/qa/captures/` for active proof and promote only the references worth handoff into `tmp/screens/`.
- Pattern: use the repo screenshot runner `scripts/qa/cdp-edge.mjs` for deterministic route loads and short click sequences.
- Pattern: if capture state becomes ambiguous, use a direct Playwright script with `ensureFreshSessionArtifactFile()` plus `buildCookiesFromArtifactSession()` to force the exact signed-in screen state and take the shot.
- Pattern: when using Playwright cookie bootstrap, do not pass both `url` and `path` to `addCookies`; strip `path` when `url` is present.
- Pattern: prefer proof from the real signed-in route first; use preview routes only when the real route is blocked or when a narrow capture harness is explicitly needed.
- Pattern: for live UI work, inspect shared component branches first and reuse the shared shell or token path before making one-off class tweaks.
- Failure Mode: the recurring fitness stale-chunk state is `Cannot find module './1682.js'` from `.next/server/webpack-runtime.js`; fix the single `:3000` runtime before doing anything else.
- Recovery Path:
  1. stop only the process listening on `127.0.0.1:3000`
  2. delete `repos/fawxzzy-fitness/.next`
  3. relaunch one server with `node scripts/dev.mjs --hostname 127.0.0.1 --port 3000`
- Failure Mode: dev and preview routes that use `useBottomActions` must be wrapped in `BottomActionsProvider`, or production deploys can fail on unrelated preview pages.
- Failure Mode: a failed production deploy on this lane is often blocked by unrelated shared or dev-route build issues; inspect the actual Vercel build error before blaming the current UI patch.
- Release-summary bullets:
  - Added the preferred real-signed-in live UI refinement lane for fitness.
  - Added the auth-artifact refresh and cookie-bootstrap pattern for reliable isolated screenshots.
  - Added the cdp-edge first, direct Playwright fallback second capture strategy.
  - Added the stale `.next` chunk recovery path as a standard repo-level repair.
  - Added the rule that preview routes using bottom actions must ship with their provider wrapper or they will poison production deploys.

## 2026-04-28 - Fitness logged-session and add-exercise UI patterns

- Rule: when the user is refining the logged-session screen, treat `view` and `edit` as the same product lane with shared shells, not separate one-off layouts.
- Rule: for history/logged-session counts, derive the visible exercise and set totals from the actually logged exercises on the screen, not from the original routine template summary.
- Pattern: the logged-session lower-half focus area should behave like one viewport shell.
  1. top focused card stays pinned
  2. middle content is the only vertical scroller
  3. bottom notes or configure surface sits just above the bottom dock with minimal dead space
- Pattern: when a set is focused in logged-session edit mode, replace the bottom note surface with the horizontal measurement rail and let the top pinned card become the set card.
- Pattern: delete actions attached to cards should reuse the same bottom-action danger intent and color treatment as the shared bottom dock delete buttons; do not restyle them separately.
- Pattern: set cards on the logged-session screen should reuse the same rounded shell language as the Today/current-session exercise cards instead of inventing a second border treatment.
- Pattern: compact exercise-card metadata that behaves like a tag count can live on the trailing rail with the chevron when the visual goal is a single right-edge cluster instead of a title-row badge.
- Pattern: metric value strings that contain list separators should render shared green-dot separators through the metric renderer, not via ad hoc text.
- Pattern: reusable editor fields with a floating top-right label should use one shared shell component so the border, label cutout, and focus treatment stay in sync across screens.
- Implementation note: the current reusable primitive is `repos/fawxzzy-fitness/src/components/ui/LabeledEditorField.tsx`.
- Pattern: the `LabeledEditorField` mask should use the app background color, not a darker chip color, so the title looks like a clean border break instead of a floating badge.
- Failure Mode: if the input focus highlight looks offset, check whether the inner input still carries its own border or ring; the wrapper shell must own the only visible border.
- Failure Mode: if the title text in a compact history header clips descenders like the `g` in `Legs`, loosen the title line-height before changing font size.
- Pattern: add-exercise for current session and edit day should continue sharing the same flow shell and goal/configure stack so future refinements land in both places together.
- Pattern: the add-exercise configure area can host horizontally scrolling measurement inputs, but the dock itself should stay width-contained; only the measurement lane should visually overflow or clip.
- Failure Mode: when the local Playwright Chromium bundle is missing, use the installed Edge channel for isolated screenshots rather than touching the user's personal browser.
- Release-summary bullets:
  - Added the logged-session viewport-shell model for pinned top card, scrolling middle content, and dock-adjacent bottom content.
  - Added the rule that history totals must reflect logged exercises, not template exercises.
  - Added the shared labeled editor field primitive and the focus/label-cutout implementation notes.
  - Added the shared delete-action and set-card styling doctrine for logged-session surfaces.
  - Added the add-exercise dock containment and horizontal measurement-lane pattern.

## 2026-04-28 - Fitness add-exercise live pass follow-ups

- Rule: when a user is approving mobile UI from screenshots, only use fresh signed-in local captures from the real route; stale fixture boards or cached filenames are not acceptable proof.
- Rule: after each live pass on fitness add-exercise, post the exact local screenshot inline and prefer a new timestamped filename when there is any risk of cache confusion.
- Pattern: the current-session add-exercise screen and the routine edit-day add-exercise screen must keep sharing the same `ExercisePicker` and goal dock path; land visual cleanup in the shared component layer first.
- Pattern: the search bar should stay pinned to the top of the real mobile scroll container, not only to a nested list wrapper; validate sticky behavior by scrolling the actual screen state after edits.
- Pattern: the configure-goal panel should sit above the blurred bottom action bar as its own fixed dock. Keep the button bar blur attached to the buttons, not spread through the whole goal panel surface.
- Pattern: the preview section should use a simple green divider plus a compact `Preview` line, and missing-goal feedback should render as `missing <metric>` until all required metrics exist.
- Pattern: add-exercise measurement titles can share the floating-label primitive positioning, but compact measurement fields may need their own label rendering treatment instead of blindly copying text-input background chips.
- Failure Mode: if the right side of the exercise cards looks wider than the left on mobile, inspect the picker viewport width and any right-only list padding before touching the card component.
- Failure Mode: if the goal field titles look clipped, confirm whether the border is visually intersecting the glyphs or whether the label span itself is clipping; they are different fixes.
- Failure Mode: screenshot harness configs that wait for removed text like `Configure goal` become silently stale after UI changes and must be updated before the next capture.
- Release-summary bullets:
  - Added the real signed-in timestamped screenshot requirement for add-exercise live passes.
  - Added the shared sticky-search, split dock, and preview-divider doctrine for the add-exercise flow.
  - Added the right-gutter diagnostic path for picker viewport width issues.
- Added the warning that compact goal-label clipping may be border intersection, stale capture state, or span clipping, and each has to be debugged separately.

## 2026-04-28 - Fitness account/settings live pass

- Rule: the account/settings screen should now behave like a focused accordion lane, not a tall stacked settings form.
- Pattern: keep one shared outer settings shell, then render only one expanded section at a time.
  1. `Data & Account`
  2. `Preferences`
  3. `Import Legacy Data`
- Pattern: when one settings section opens, hide the sibling sections from the visible stack so the expanded section owns the vertical space, similar to the focused-card behavior used on logged-session detail.
- Pattern: collapsed settings sections should render as centered disclosure cards with:
  - centered title
  - chevron anchored bottom-right
  - no extra subtitle/body text in the collapsed state
- Pattern: expanded settings sections should drop the inner secondary border shell; keep the outer section card border only and let the inner controls sit on the shared screen surface.
- Pattern: settings save actions should only look active when there is an unsaved change since the last successful save, not merely a change from the original server props.
- Pattern: account header identity should be centered and render:
  - `username | email` when a username exists
  - `email` only otherwise
- Pattern: for this screen, username fallback should use the same lane as the account form:
  - auth metadata username/display_name first
  - remembered login display name next
  - derived email local-part fallback last
- Pattern: the preferences section keeps the segmented side-by-side control language, but the labels should be centered directly above their control groups.
- Pattern: legacy import is a single-action flow in the UI now.
  - user provides legacy email and password
  - one button runs export, import, and parity in sequence
  - raw snapshot JSON is no longer exposed in the normal mobile UI
- Pattern: destructive or status tags on the settings screen should use the plain signature-meta tag style, not pill chips, unless they are part of a true action control.
- Implementation note: the client accordion owner is:
  - `repos/fawxzzy-fitness/src/components/settings/SettingsAccordionClient.tsx`
- Implementation note: the client header identity fallback is:
  - `repos/fawxzzy-fitness/src/components/settings/SettingsHeaderIdentity.tsx`
- Failure Mode: if a capture script assumes sibling sections remain in the DOM after one section expands, it will fail after the focused-accordion refactor. Reopen the page fresh for each expanded-state screenshot.
- Failure Mode: a server-rendered header cannot see remembered local login state. If the mobile header needs the remembered name, move that identity row into a small client component instead of trying to patch server-only metadata reads.
- Release-summary bullets:
  - Added the focused-account accordion model for settings.
  - Added the single-action legacy import rule and removed raw snapshot exposure from the normal mobile flow.
  - Added the centered username/email header fallback chain.
  - Added the rule that save buttons must gray back out after a successful save baseline resets.

## 2026-04-25 - Launcher routes, target app installs

- Rule: a launcher routes users to the target app's canonical install route; the target app owns installability, iOS gates, and standalone access truth.
- Rule: a native PWA install button may only exist for the current origin after `beforeinstallprompt` has fired.
- Pattern: use a split platform flow.
  1. iOS in-app browser: hard gate with `Open in Safari` and copy link.
  2. iOS Safari browser tab: hard gate with `Share, then Add to Home Screen`.
  3. iOS standalone/Home Screen: allow normal access.
  4. Android and other non-iOS browsers: allow access and show native install UI only when the browser exposes it.
- Failure Mode: do not treat `localStorage` or `sessionStorage` as installed truth.
- Failure Mode: do not label cross-origin navigation as `Install`.
- Failure Mode: do not wrap the entire app shell when browser auth and recovery routes must remain usable in-browser.
- Failure Mode: browser automation can prove app logic and mocked install states, but real iOS Add to Home Screen and real Android native install prompts still need manual device QA.
- Release-summary bullets:
  - Added launcher-to-target-app installer routing doctrine for cross-origin PWAs.
  - Added the iOS in-app browser, Safari, and standalone access-gate pattern.
  - Added the rule that native install CTAs are current-origin only and capability-gated.
  - Added runtime standalone detection as the installed-state source of truth.
  - Added manual-device QA as a required final step for real install flows.

## 2026-04-23 - Fitness auth must not own install acquisition

- Rule: app auth flow must not own install acquisition UX when install is handled externally.
- Pattern: auth/recovery routes should keep one shared shell with inline status and error messages instead of branching into screen-per-state variants.
- Failure Mode: install-first route branching and standalone recovery error screens create extra state surfaces, stale capture-map truth, and mobile UI drift for flows that should stay message-level.

## 2026-04-23 - Fitness release lanes require manual _stack deploys and reusable QA auth

- Type: Guardrail
- Summary: Fitness deploy and QA work must use `_stack` deploy entrypoints, keep Vercel Git auto-deploy creation disabled, and verify auth-aware local flows with one permanent Supabase QA user instead of random signup users.
- Suggested Playbook File: docs/GUARDRAILS/fitness-auth-deploy-qa-lane.md
- Rationale: Prevents repeated auth/deploy chaos where throwaway users accumulate, local browser and server Supabase env drift apart, Git-triggered Vercel deploys silently reappear, or deploys run from the wrong repo boundary.
- Evidence: repos/_stack/ops/Test-FitnessDeployLink.ps1, repos/_stack/ops/Test-FitnessDoctor.ps1, repos/fawxzzy-fitness/scripts/qa/fitness-qa-user.mjs, repos/fawxzzy-fitness/scripts/qa/fitness-local-feedback.mjs
- Status: Proposed

## Deploy identity guards

- Production deploy guards should validate the configured live hosting identity for the current lane, not a guessed future owner or namespace.
- For Vercel-backed repos, keep the expected scope and project in checked-in operator config and allow explicit environment overrides for one-off validation.
- Treat visible team-label cleanup and namespace changes as separate lanes. Namespace changes can alter future generated hosting URLs and should not be bundled into an unrelated production deploy.
- Hosting identity checks must validate immutable team/project IDs, not only mutable slugs or display names.
- Use connector-confirmed project identity as source of truth, then mirror that identity into operator deploy guards and repo-local `.vercel/project.json` metadata.
- Failure Mode: A team rename makes slug-only checks lie, which looks like a wrong-owner failure even when the linked Vercel project is correct.
- If Vercel sees the correct team and project but a fresh pushed SHA creates no deployment object, classify it as a Git integration ingestion failure before diagnosing app code or retrying production deploys from the CLI.
- After connector repair, prefer one fresh Git-triggered branch deployment as the proof path; only resume production shipping after Vercel creates and runs that branch deployment from Git.
- Failure Mode: Repeated CLI production retries can mask the real issue when Git-connected preview creation is disabled or dead, which makes an ingestion outage look like an app or build failure.
- Failure Mode: A mounted app folder under the ATLAS stack root inherits the parent repo boundary and poisons Git recovery until the app is recloned as a real standalone repo.
- Failure Mode: Windows prebuilt deploy fallback can fail on symlink packaging; do not diagnose app code from that signal alone.

## 2026-05-11 - QA release governance

- Rule: Repo lint failures are repo-owned blockers; root QA should surface them, not bypass them.
- Rule: Manual attestation may satisfy physical/manual review, but it must never be labeled as automated provider proof.
- Rule: Promotion wording must match the evidence profile that actually passed.
- Rule: Fitness must remain non-release-ready until real manual or provider-backed physical evidence exists.
- Rule: No-credential provider readiness must never produce a false physical pass.
- Rule: Release readiness must match the target SHA or stack lock pin, not just a recent receipt.
- Rule: Release readiness may also require a trusted receipt origin when the release profile enables it.
- Pattern: Release readiness is repo-tier specific; physical-device proof belongs to release-critical web flows, not every repo.
- Pattern: Release policy turns QA receipts into operational gates.
- Pattern: Local receipts prove logic; CI or protected receipts prove release trust.
- Pattern: Receipt selection should prefer strongest valid evidence, not just newest evidence.
- Pattern: Adoption drift scanning prevents root prototypes from masquerading as real child-repo adoption.
- Pattern: Prototype QA configs must be explicitly labeled, adopted, or retired.
- Pattern: Rehearse release gates with both passing and intentionally blocked repos.
- Pattern: Warning-budget reporting gives governance debt shape before turning it into hard enforcement.
- Failure Mode: Once release readiness exists, stale receipts can create false confidence unless adoption freshness is checked.
- Failure Mode: Fresh receipts for the wrong commit can create false release confidence.
- Failure Mode: Correct-SHA receipts can still be weak if they were produced outside the trusted release path.
- Failure Mode: A newer `local_dev` receipt can overshadow a stronger trusted release receipt unless evidence ranking is explicit.
- Failure Mode: Windows `.pyc` cache write failures can create false verification noise unless cache hygiene is part of the verification path.
- Failure Mode: Treating `warning_count=559` as harmless forever turns governance debt into background noise.
- Failure Mode: Using one generic promoted label hides whether a repo passed package, docs, web visual, manual physical, or provider physical evidence.
