# Playbook Notes

## 2026-05-27 - Operator-grade governance doctrine still needs explicit invariants and trust semantics before ratification

- Rule: ATLAS may project, index, verify, and coordinate; it may not silently absorb implementation ownership or mutable child state.
- Rule: adoption is not verification.
- Rule: transcript residue is not memory.
- Rule: Cortex memory must be provenance-backed.
- Rule: Lifeline is threshold-triggered, not identity-driven.
- Pattern: coordination-only root -> owner-truth child repos -> provenance-backed memory -> explicit verification authority -> ratified governance only after trust-class and exception normalization.
- Failure Mode: governance language sounds precise enough to feel final while still drifting because owners, trust classes, exception records, and metric contracts remain implicit.
- Release-summary bullets:
  - Packaged the ratification review durably instead of leaving it in chat.
  - Elevated the reusable invariants that should constrain future doctrine work.
  - Preserved the distinction between a strong v1 draft and final governed doctrine.

## 2026-05-27 - Durable context must externalize out of volatile worker continuity

- Rule: External Context First.
- Rule: when a lane has a maintained continuity manifest, retrieve it before trusting chat recap or remembered session state.
- Pattern: Ephemeral Worker, Durable Substrate.
- Pattern: continuity manifest -> receipt chain -> owner truth surfaces -> verification/adoption surfaces -> chat nuance last.
- Failure Mode: Recursive Context Rot Loop.
- Failure Mode: a continuity manifest that starts copying owner truth instead of pointing to it becomes a second truth store and recreates drift under a more official name.
- Durable Context Externalization: tracks whether critical continuity is reconstructable from ATLAS and owner-repo artifacts rather than trapped in GPT/Codex chats, prompt carryover, or operator memory.
- Release-summary bullets:
  - Added Durable Context Externalization as a first-class marker instead of leaving continuity durability implicit inside knowledge-capture or book-quality lanes.
  - Froze the doctrine that workers should retrieve durable context before trusting chat continuity.
  - Named the recursive context-rot failure mode so future lanes can distinguish durable continuity from conversational carryover.

## 2026-05-27 - Prompt packs should resume from durable context, not transcript continuity

- Rule: canonical continuation prompts should treat prior chat continuity as non-authoritative.
- Rule: active restart surfaces should prefer continuity manifests, receipt chains, truth maps, promoted notes, and owner verification/adoption surfaces before transcript recap.
- Pattern: continuity manifest -> current book chapter -> receipt chain -> owner truth surface -> verification/adoption surface -> transcript nuance last.
- Failure Mode: a restart prompt that still trusts remembered session state before durable retrieval recreates stale package ordering and wrong-lane continuation drift.
- Release-summary bullets:
  - Normalized the active ATLAS continuation pack so retrieval-first doctrine is expressed consistently instead of only implied.
  - Removed stale restart guidance that still pointed at older Local Data Gateway package ordering.
  - Reinforced that transcript carryover is optional nuance, not a canonical restart substrate.

## 2026-05-27 - Manifest-backed continuity requires active restart routing, not just manifest doctrine

- Rule: a lane may claim `manifest-backed` continuity only when an active ATLAS-root manifest points to the current decisive receipt, owner truth surfaces, and relevant verification/adoption surfaces.
- Rule: continuity manifests are adoption-ready first for cross-repo or cross-surface lanes with dense receipt chains and non-trivial owner routing.
- Pattern: restart guide -> active continuity manifest -> governing receipt chain -> owner truth surface -> verification/adoption surface -> transcript nuance last.
- Failure Mode: calling a lane `manifest-backed` before restart can actually follow the manifest chain turns continuity doctrine into label theater.
- Release-summary bullets:
  - Froze the difference between a manifest contract existing and a lane actually being manifest-backed.
  - Named the first-adoption lane set for continuity-manifest seeding without pretending those manifests already exist.
  - Preserved root as continuity routing only while keeping owner repos as truth owners.

## 2026-05-27 - Local data gateway proof packaging matures evidence, not handoff authority

- Rule: local proof packaging is evidence packaging, not handoff authorization.
- Rule: marker movement after proof packaging requires real-workflow proof that the packaged bundle preserves explicit no-send, no-execution, no remote-target, and no automatic-handoff state.
- Pattern: contract -> validator -> dry-run emitter -> local review -> local proof package -> proof receipt -> marker ratchet.
- Failure Mode: treating a packaged proof bundle as implied permission to send, sync, post, or execute downstream work collapses evidence packaging into hidden transport authority.
- Release-summary bullets:
  - Added the rule that proof packaging strengthens local evidence maturity without opening handoff authority.
  - Preserved the send boundary by requiring explicit proof that packaged bundles still record no-send and no-authorization state on real workflows.

## 2026-05-27 - Local data gateway review proof ratchet requires explicit no-send approval evidence

- Rule: local packet review is a governance checkpoint, not transport authority.
- Rule: marker movement after review requires proof that approval remains local-only and records explicit no-send and no-execution attestation on real workflows.
- Pattern: contract -> validator -> dry-run emitter -> local review -> proof receipt -> marker ratchet.
- Failure Mode: treating a local `approved` disposition as implied authorization for downstream send or execution collapses the review boundary into hidden transport logic.
- Release-summary bullets:
  - Added the rule that review-proof maturity depends on explicit no-send and no-execution attestation, not just the existence of a review helper.
  - Preserved the local-first boundary by separating review maturity from any future handoff or send lane.

## 2026-05-27 - Local data gateway is now admitted doctrine, not only a marker idea

- Rule: raw data lands locally first, and downstream systems receive purpose-built packets rather than messy raw input by default.
- Rule: a governed packet must carry purpose, schema/version, sensitivity, provenance, transformation record, validation result, redaction status, dedupe status, exclusion summary, receipt/proof reference, and minimum useful payload.
- Rule: packet quality depends on proving what stayed local, not only what was exported.
- Rule: the first `_stack` helper boundary must stay local-only with `preview`, `emit`, and `validate` modes, and must not include `send`, `sync`, `post`, `submit`, or `mutate`.
- Rule: marker movement beyond the first doctrine ratchet requires live helper proof on real workflows, not just packet doctrine or helper existence.
- Pattern: local source -> packet contract -> real-workflow exemplar proof -> helper contract -> implementation planning -> local-only helper.
- Pattern: validator proof -> dry-run emitter proof -> marker ratchet only after no-send local artifact behavior is proven on real workflows.
- Failure Mode: moving the marker or helper ambition forward before a reusable packet contract, exemplar proof, and helper boundary are all durable confuses doctrine maturity with implementation maturity.
- Failure Mode: moving the marker because the emitter exists, without proving its no-send local artifact behavior on real workflows, mistakes implementation presence for reusable governed behavior.
- Release-summary bullets:
  - Admitted Local Data Gateway as durable doctrine rather than a marker-only idea.
  - Froze the required packet field set and the no-send helper boundary.
  - Limited the first honest marker move to a small doctrine-plus-proof ratchet rather than claiming implementation readiness.

## 2026-05-26 - Local data gateway should be a first-class stack marker

- Rule: raw data lands locally first; remote systems receive purpose-built packets.
- Rule: local preprocessing must happen before data leaves the machine or repo boundary for a model, API, SaaS tool, remote database, automation, teammate, or shared system.
- Rule: exported payloads should carry purpose, schema or version, sensitivity label, source or provenance, transformation record, and minimum useful payload shape.
- Pattern: raw input -> local normalize, validate, redact, classify, dedupe, extract -> minimum useful payload -> remote refinement, sync, collaboration, or specialized processing.
- Failure Mode: sending messy raw data directly to an AI, API, SaaS tool, or remote database creates privacy risk, token waste, duplicate state, and weak provenance.
- Failure Mode: repeated local preprocessing that never graduates into command surfaces recreates the same manual cleanup debt in every lane.
- Local Data Gateway: tracks whether raw data is processed locally before export and whether repeated local preprocessing becomes governed reusable command surface.
- Release-summary bullets:
  - Added Local Data Gateway as a first-class convergence marker instead of leaving it as a hidden sub-note inside secret hygiene or data hygiene lanes.
  - Defined the local-by-default boundary and the minimum payload contract for exports to remote systems.
  - Connected the marker to secret hygiene, Supabase hygiene, automation graduation, core pattern spread, and truth-map doctrine.

## 2026-05-24 - Playbook origin and research trail should stay explicit

- Rule: Playbook is not another AI coding assistant; it is the deterministic repo runtime and trust layer between humans or AI agents and real repositories.
- Rule: verify before plan; plan before apply; apply before trust renewal.
- Rule: mutation follows trust, not curiosity.
- Rule: declared mutation scope must be enforced before apply succeeds.
- Rule: knowledge must be promoted before it influences execution.
- Rule: research doctrine and implemented runtime truth are separate layers.
- Rule: CI is a release gate, not a place.
- Rule: measure outcomes, not activity.
- Rule: unsafe speed is not value.
- Pattern: verify -> plan -> apply -> verify.
- Pattern: state -> transformation -> enforcement.
- Pattern: evidence -> compaction -> promoted doctrine -> bounded execution.
- Pattern: declare scope -> enforce scope -> mutate -> receipt.
- Pattern: local receipt -> optional publish sync -> optional deployment handoff.
- Pattern: start read-only, expand by evidence.
- Pattern: state -> narrative compression.
- Failure Mode: AI mutation without evidence boundaries.
- Failure Mode: command-surface drift between roadmap, generated docs, CLI help, and actual runtime behavior.
- Failure Mode: correct-but-dense truth reduces adoption even when the underlying system is technically right.
- Failure Mode: research-as-status lets speculative theory masquerade as implemented runtime capability.
- Failure Mode: advisory scope bundles mistaken for real safety.
- Release-summary bullets:
  - Consolidated the Playbook origin story and research trail into one root-owned continuity artifact.
  - Reaffirmed the canonical remediation loop as `verify -> plan -> apply -> verify`.
  - Preserved the distinction between research doctrine, architecture framing, and live runtime truth.
  - Captured the strongest reusable rules, patterns, and failure modes as stack-readable doctrine.
- Continuity reference: `docs/ops/PLAYBOOK-ORIGIN-RESEARCH-TRAIL-2026-05-24.md`

## 2026-05-24 - Core pattern convergence should be its own lane

- Rule: strong reusable ideas should not stay trapped inside one repo, one workflow, or one operator habit when they clearly belong across the stack.
- Rule: capturing patterns is not the same as spreading them; documentation alone does not prove convergence.
- Rule: Playbook should hold reusable doctrine, while ATLAS should show where that doctrine applies and who owns each implementation boundary.
- Pattern: extract reusable rule or pattern -> map owner and applicability -> route into doctrine and stack docs -> verify later adoption in implementation lanes.
- Failure Mode: a stack can look well-documented while still behaving like isolated local habits because the best ideas never actually spread.
- Failure Mode: treating Playbook Everywhere + Cortex Interface as sufficient hides whether the strongest ideas from Fitness, Lifeline, `_stack`, QA, release, or Discord have converged into shared practice.
- Release-summary bullets:
  - Added Core Pattern Convergence as a separate lane from knowledge capture and interface adoption.
  - Defined the lane as stack-wide spread of reusable rules, patterns, and failure modes.
  - Preserved the split between doctrine capture, doctrine visibility, and actual cross-stack application.

## 2026-05-24 - Repeated AI work should graduate into explicit automation lanes

- Rule: repeated Codex, AI, or operator asks should be noticed, classified, and routed toward safe automation instead of being re-executed manually forever.
- Rule: automation graduation is separate from long-run AI batching; one lane turns repetition into commands, while the other governs bounded multi-step job execution.
- Rule: only safe, reviewable, owner-clear workflows should graduate into `_stack`, Playbook, or bot command surfaces.
- Pattern: repeated request -> repetition receipt or marker -> owner and risk classification -> narrow command contract -> verification and rollback path -> documented operator surface.
- Failure Mode: leaving repeated mechanical work in chat burns context and tokens while hiding the real opportunity for durable command surfaces.
- Failure Mode: turning an unstable or ambiguous workflow into a command too early just automates confusion.
- Release-summary bullets:
  - Added the doctrine that repeated AI and operator work should feed an explicit automation-conversion lane.
  - Distinguished repetition-to-automation from long-run batch orchestration.
  - Added the rule that new command surfaces require owner clarity, verification, and rollback paths.

## 2026-05-17 - Discord moderation should stay reversible and explicit

- Rule: community moderation should escalate through logged notice and warning lanes before punitive action whenever possible.
- Rule: default Discord moderation should isolate through reversible role and channel changes, not through bans, kicks, or message deletion.
- Rule: every moderation action must create or update a case record and keep a release or resolution path.
- Pattern: notice or warning -> logged case -> Purgatory isolation if needed -> release or warning-clear -> safe role restoration.
- Pattern: during Purgatory, remove access roles such as `Verified`, preserve unrelated non-access roles, and show only the Purgatory category and channel.
- Pattern: branded moderation messages may DM the target fail-soft, but delivery failure must never block the case write or role transition.
- Failure Mode: production behavior must not live only on an unmerged branch; merge the live-tested moderation polish back into `main` before treating it as stack truth.
- Failure Mode: silent bans, destructive moderation, or missing restore paths create drama and make recovery harder than the original incident.
- Release-summary bullets:
  - Added the reversible Discord moderation doctrine with notice, warning, Purgatory, and release lanes.
  - Added the rule that moderation changes must remain logged, restorable, and no-ban-by-default.
  - Added the explicit merge-back requirement when a live moderation polish ships from a branch first.

## 2026-05-17 - Discord shipped-card promotion should use one public format only

- Rule: a shipped Discord feedback card gets one public updates-channel post, not multiple overlapping update formats.
- Rule: thread audit comments stay compact and operational inside the feedback thread.
- Rule: when a specific feedback card ships, the public updates-channel post should use the short `Update:` card-promotion format and end with `Report ID: <short id>`.
- Rule: do not also publish the broad `@everyone` release-summary template for that same shipped card unless the owner explicitly wants a separate aggregate release note.
- Pattern: shipped card -> compact thread audit comment -> one public card-promotion update post.
- Failure Mode: mixing thread-audit copy, broad release-summary copy, and card-promotion copy for the same shipped card creates duplicate logic and confusing public history.
- Status: Proposed

## 2026-05-17 - Discord community ops should keep one board and low-noise channels

- Rule: the Discord feedback board is the visible community board, not a second task system.
- Rule: feedback card mutations stay in the forum thread as audit comments and board export artifacts; they do not auto-post to updates, ATLAS, or GitHub.
- Rule: only `Updates` and `Main` are loud channels; other Discord workflows should avoid broad pings by default.
- Rule: the bot must not claim it can force user-level channel or category mute settings, because those are personal Discord client preferences.
- Pattern: feedback forum card -> audit comments -> board export -> reviewed Verta Core / Playbook planning input -> curated Update Bot promotion if user-facing.
- Pattern: server inventory -> noise audit -> conservative dry-run recommendations -> reviewed permission or mention changes.
- Pattern: moderation escalates through notice or warning -> logged case -> reversible Purgatory isolation if needed -> release or warning-clear.
- Failure Mode: duplicating raw Discord cards into ATLAS or GitHub creates conflicting task truth and noisy sprint churn.
- Failure Mode: claiming the bot can mute channels for users hides the real permission and allowed-mentions model.
- Release-summary bullets:
  - Added the one-board, reviewed-promotion Discord workflow doctrine.
  - Added the low-noise rule that only `Updates` and `Main` are loud channels.
  - Added the rule that inventory and audit tooling should enforce mention and permission truth without fake personal-mute claims.

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

## 2026-05-22 - Branch discipline for root-launched Codex lanes

- Rule: no Codex lane starts until the owner repo and the target branch or worktree are explicit.
- Rule: use clean worktrees for repo-specific lanes.
- Rule: use ATLAS root branches only for stack-root docs, projection, standards, audits, and cross-repo coordination slices.
- Pattern: root lane decides owner repo -> owner repo or root worktree is named -> target branch is named -> work starts only inside that declared surface.
- Pattern: if a lane is repo-specific, prefer an isolated worktree over reusing whatever branch was already active in another chat.
- Failure Mode: starting multiple Codex chats from the ATLAS root without an explicit owner repo and target branch lets unrelated work inherit the active branch and creates mixed replay branches that are hard to classify later.

## 2026-05-22 - AI long-run batch orchestration must stay bounded and supervisor-led

- Rule: long-run AI batching is a job-oriented orchestration problem, not an invitation to keep one giant interactive Codex session alive indefinitely.
- Rule: unattended or multi-hour batching should use bounded jobs, isolated worktrees, durable checkpoints, and explicit verification gates.
- Rule: root doctrine may define the lane and contracts first, but `_stack` should own execution-oriented orchestration contracts and Playbook should own reusable verification and workflow doctrine.
- Pattern: research -> root doctrine -> lane or job contract -> supervised single-lane pilot -> only then wider unattended batching.
- Pattern: each batch job should declare owner repo, target worktree, allowed write scope, checkpoint surface, and exit verification before execution begins.
- Failure Mode: treating one large interactive ATLAS-root session as the default batching model recreates branch contamination, weakens verification boundaries, and hides partial failures until the lane is too large to review safely.
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

## 2026-05-22 - Stack lock regeneration must wait for root normalization

- Rule: do not repair or regenerate `stack.lock.yaml` while the ATLAS root is behind `origin/main` and preserved recovery residue is still intentionally present.
- Rule: lock refresh belongs after preservation classification and root reconciliation, not during transitional branch-normalization posture.
- Pattern: preserve replay evidence -> classify archive or recovery or package ownership -> reconcile root with `origin/main` -> regenerate `stack.lock.yaml` -> rerun validation.
- Failure Mode: refreshing the lock during a dirty or transitional root phase bakes temporary branch, residue, or preservation state into the pinned stack contract.

## 2026-05-22 - Strategic convergence lanes must be explicit near the front of the program

- Rule: strategic lanes are part of the convergence program, not separate random work.
- Rule: Vision Consolidation belongs near the front so later cleanup and convergence work optimize toward the real endgame instead of local hygiene only.
- Rule: long-run doctrine lanes should be recorded in marker docs before implementation or cleanup widens.
- Pattern: Vision Consolidation -> Inventory & Truth Map -> Branch & Worktree Normalization -> Workflow Convergence -> Dependency Untangling -> later adoption and publication lanes.
- Pattern: every strategic lane should answer the same five questions:
  - why does this exist
  - what is the endgame
  - what does done look like
  - how does it align with ATLAS
  - what should we stop doing
- Vision Consolidation: defines the endgame, purpose, done-state, and ATLAS alignment for every lane.
- Cortex Integration into Playbook: tracks how Cortex planning or admission work becomes Playbook-readable doctrine, contracts, patterns, or validation logic without moving runtime ownership too early.
- Knowledge Capture: tracks whether key reasoning, rules, patterns, failures, and decisions are recorded in durable docs instead of trapped in chat.
- Feedback Loop Readiness: tracks whether each lane can receive, process, and route user or system feedback into ATLAS, Playbook, Discord, or repo workflows.
- Truth Map Book: consolidates documentation, roadmaps, notes, systems, concepts, and lane maps into one definitive cross-referenced guide.
- Dependency Untangling: tracks hidden coupling between lanes and reduces it so future Fitness, Discord, and ATLAS work can run in parallel safely.
- Knowledge Transfer Readiness: tracks whether a future teammate, Codex worker, or Cortex agent could continue the work from docs and receipts.
- Future Self Alignment: periodic review that today’s work still serves the long-term vision.
- Sandbox Simulation Readiness: ensures each lane has safe places to test bold ideas without risking core systems.

## 2026-05-15 - Discord verification, member numbers, and future bot doctrine

- Type: Pattern
- Summary: Discord should display source-app truth through signed Fitness-hosted interactions, durable member links, and governed side effects rather than running a local bot as system authority.
- Current truth:
  - Active: Fitness-hosted Discord HTTP interactions endpoint
  - Prototype/fallback only: `fawxzzy-fitness-discord-bot` Gateway bot
  - Identity authority: Fitness plus Supabase profiles
  - Discord responsibilities: signed interaction transport, modal UI, role display, nickname display
  - Playbook and ATLAS responsibilities: patterns, receipts, triage, reviewed promotion, not noisy automatic writes
- Rule: Fitness owns identity; Discord consumes proof.
- Rule: Email knowledge is not identity proof.
- Rule: Unsigned Discord interaction payloads must never reach role-grant logic.
- Rule: Public member numbers compact from `#1` while Zac remains `#0`.
- Rule: Automation accounts must not consume public member numbers.
- Rule: Discord bug reports should be queued and triaged before becoming repo truth.
- Rule: Release posts must be curated for users, not copied from internal logs.
- Pattern: Authenticated Fitness session -> one-time token -> signed Discord modal submit -> token consume -> role grant.
- Pattern: Fitness profile number -> Discord member link -> nickname sync.
- Pattern: Discord support modal -> structured DB queue -> Playbook triage -> reviewed issue or task.
- Pattern: Release ledger or PRs -> curated release copy -> Discord announcement.
- Failure Mode: Local Gateway bots, email-only checks, or auth middleware redirects make Discord verification unavailable or unsafe.
- Failure Mode: Discord owner or higher-role users verify correctly but cannot be renamed by the bot.
- Failure Mode: Changing DB member numbers without Discord resync leaves stale nicknames.
- Failure Mode: Direct Discord-to-repo writes create noisy or abusive history.
- Failure Mode: Raw technical release posts are hostile to normal users.
- Future backlog:
  - Bug Report Bot should use a signed Discord modal, store structured reports in Supabase, and enter a review queue before any Playbook, ATLAS, or GitHub promotion.
  - Curated Release Bot should publish only admin-approved user-facing updates and must not dump raw deploy logs, migrations, or internal changelog noise.
- Evidence: Fawxzzy Fitness Discord verification build, PR #20, PR #21, PR #22
- Status: Proposed

## 2026-05-16 - Discord community systems should close operations and doctrine before more bots ship

- Rule: finish the operating system before adding another bot.
- Rule: Discord is the community surface, not the ATLAS control plane.
- Rule: deployment metadata is input, not release copy.
- Rule: feedback attachments are Discord-hosted evidence, not app DB blobs.
- Rule: optional Discord decoration must fail soft.
- Rule: database triggers do not call Discord.
- Pattern: production proof -> doctor command -> migration reconciliation -> docs truth -> doctrine update -> next feature.
- Failure Mode: stacking more Discord features on undocumented production lessons creates brittle automation and stale docs.

## 2026-05-16 - Supabase migration ledger repair should require schema evidence

- Rule: migration ledger repair requires schema evidence first.
- Pattern: verify production effects -> repair exact versions -> validate -> document.
- Failure Mode: blind migration repair makes the ledger claim schema history that production does not actually have.

## 2026-05-22 - Marker consolidation should reduce noise without losing concepts

- Rule: every future report ends with the full marker table, including future lanes at `0%`.
- Rule: marker names should stay consolidated when multiple names describe the same endgame.
- Pattern: keep historical completion markers separate, but collapse overlapping future-program markers into one stronger dashboard line.
- Unified Workflow Convergence: combines overall integration, workflow convergence, Discord workflow unification, QA/LLEL workflow convergence, Fitness workflow integration, and `_stack` integration.
- Truth Map & ATLAS Book: combines documentation connection web, Truth Map Book, and ATLAS Book.
- Playbook Everywhere + Cortex Interface: combines Playbook Everywhere Adoption with Cortex Integration into Playbook.
- Knowledge Capture & Transfer: combines knowledge capture and knowledge transfer readiness.
- Vision & Future Alignment: combines Vision Consolidation and Future Self Alignment.
- Full Stack Re-sync, Clean & Closeout: combines broad re-sync/clean work with final cleanup closeout.
- Discord Workflow & Documentation Publishing: combines Discord workflow consolidation with documentation channel publishing.
- Post-Convergence Lane Split Readiness: combines split preparation with future Fitness, Discord, and ATLAS lane readiness.
- Failure Mode: marker sprawl makes the dashboard noisy enough that operators stop trusting it even when the underlying ideas are correct.

## 2026-05-23 - Canonical source and tmp dependency risks need first-class convergence markers

- Rule: canonical repo truth must not drift into `tmp/`, deploy clones, or operator recovery worktrees.
- Rule: duplicate source surfaces, branding sources, Discord publication reliability, secret hygiene, and manual deploy exceptions are convergence blockers, not side tasks.
- Pattern: restore canonical repo roots first -> eliminate hidden `tmp/` dependency second -> decommission duplicate surfaces third -> only then widen cleanup and workflow convergence.
- Canonical Repo Restoration: tracks whether canonical repo roots exist again under `repos/`, especially Fitness, and whether production workflows truly point there.
- Duplicate Surface Decommission: tracks duplicate or orphaned source surfaces until each is removed, archived, retained as evidence, or routed into a canonical repo.
- Tmp Dependency Elimination: tracks removal of production-critical dependence on `tmp/` worktrees, deploy clones, and preservation checkouts.
- Brand Asset Canonicalization: tracks whether ATLAS owns the single canonical branding source and downstream apps consume reproducible generated outputs.
- Preview Cache & Surface Consistency: tracks whether deployed icon, preview, PWA, and share surfaces match the canonical branding source and can be verified cleanly.
- Operator Secret Path Hygiene: tracks whether secret-backed operator flows avoid spilling env or secret residue into repo roots.
- Manual Deploy Exception Burn-Down: tracks the remaining risk from direct deploy behavior outside `_stack`.
- Discord Workflow, Publication & Docs Reliability: combines Discord workflow reliability, `#updates` posting stability, fallback path clarity, and documentation-channel publication into one durable marker.
- Failure Mode: if canonical repos, deploy truth, and `tmp/` dependency are not fixed before broader convergence, the stack keeps recreating the same wrong-repo, wrong-branch, wrong-deploy confusion.

## 2026-05-24 - Marker model should absorb Discord OS separation and data hygiene explicitly

- Rule: when a cross-stack cleanup concern is really infrastructure ownership or data-governance work, it should get a durable marker instead of hiding inside a vague future lane.
- Rule: stale Vercel project and deployment surfaces belong under existing deploy-authority and duplicate-surface lanes, not under a new one-off marker.
- Pattern: reuse an existing marker when the work is fundamentally duplicate-surface or deploy-authority cleanup; add a new marker only when the concern has distinct ownership, sequencing, and done-state.
- Discord OS Infrastructure Separation: supersedes the older Discord OS extraction-review framing and tracks separation of Discord OS code, Vercel, Supabase, env ownership, and shared-data contracts away from Fitness-hosted default coupling.
- Fitness Supabase Profile/Data Hygiene: tracks inventory, cleanup planning, and governance of Fitness auth/profile/data surfaces, especially unknown, duplicate, and automation-linked identities.
- Duplicate Surface Decommission and Manual Deploy Exception Burn-Down should both explicitly absorb stale Vercel surface cleanup targets when those surfaces can confuse source truth or deploy authority.
- Failure Mode: if Discord OS separation and Fitness data hygiene stay implicit, later cleanup mixes repo, deploy, bot, and identity concerns into one vague migration lane and raises breakage risk.
