# ATLAS UI Visual Proof

## Purpose

ATLAS visual proof complements the existing semantic observer and drift validator. It does not replace owner-truth contracts.

- Rule: image proof complements semantic contract validation; it does not replace owner-truth contracts.
- Pattern: semantic drift checks structure, visual proof checks landed appearance.
- Failure Mode: using free-form screenshot judgment instead of deterministic diff rules creates flaky, untrustworthy gates.

## Model

The visual proof lane is root-owned and validator-only.

- Fitness remains the source of UI truth.
- ATLAS semantic observation still resolves owner tokens and primitive variants.
- Visual proof compares declared image captures against approved reference images with deterministic assertions.

Completion should be treated as:

1. owner-repo verify passes
2. semantic observer/drift passes
3. visual proof passes for the touched capture set

ATLAS now also derives a combined proof summary for machine consumers:

- `runtime/atlas/ui-proof/fitness/latest.json`
- `runtime/atlas/ui-proof/fitness/latest.md`

That summary is a compatibility projection only.

- Rule: combined proof status is derived, not hand-authored.
- It is not a replacement for the underlying semantic drift or visual proof owner artifacts.
- `_stack`, cockpit, and other consumers should read the combined summary when they need one completion-ready signal, but they should still retain refs back to the underlying reports.

## Manifest

The active manifest lives at:

- `ops/atlas/ui_visual_proof/fitness_visual_proof.v1.json`

The manifest declares:

- the owner repo and capture map
- the current screenshot artifact root
- the approved reference image root
- the captures that are currently proof-gated
- the assertion kind for each capture
- optional stale-proof guards like `expected_capture_map_digest` and `expected_observation_digest`

Supported assertion kinds:

- `unchanged`
- `changed_expected`
- `changed_only_within_mask`
- `max_visual_delta`
- `min_visual_delta`

## Current Opted Captures

The currently proof-gated captures are:

- `settings-overview-default`
- `today-overview-default`
- `routines-overview-default`
- `history-sessions-list-default`
- `history-exercises-default`
- `workout-card-session-summary-card`
- `detail-support-exercise-info-sheet`

All seven are currently baselined as `unchanged`.

- `settings-overview-default` is the stable control surface.
- `today-overview-default` is the first high-signal Today surface tied to the active adoption rail, including the shared list rhythm and feedback chrome now published through the owner token bridge.
- `routines-overview-default` extends the proof lane across the shared main-tab family so the Routines-active state is explicitly baselined instead of inferred from Today, History, and Settings alone.
- `history-sessions-list-default` extends the proof lane into the history session-summary family.
- `history-exercises-default` extends the proof lane into the history exercise-browser family.
- `workout-card-session-summary-card` extends the proof lane into the workout-card/session-summary family.
- `detail-support-exercise-info-sheet` extends the proof lane into the adopted exercise-detail support family.

The approved references are seeded from the repo's existing deterministic mobile-regression flow at `393px`, then copied into the root-owned proof locations.

- `settings-overview-default` maps to the `settings-default` mobile-regression scenario.
- `today-overview-default` maps to the `today-default` mobile-regression scenario.
- `routines-overview-default` maps to the `routines-current-view` mobile-regression scenario.
- `history-sessions-list-default` maps to the `history-sessions-compact` mobile-regression scenario.
- `history-exercises-default` maps to the `history-exercises-compact` mobile-regression scenario.
- `workout-card-session-summary-card` maps to the `today-in-session-summary` mobile-regression scenario.
- `detail-support-exercise-info-sheet` maps to the `exercise-detail-strength` mobile-regression scenario.
- Pattern: when owner screenshots for the exercise discovery/detail family still land on those two deterministic scenarios, keep root proof attached to the existing capture ids instead of cloning a new exercise-detail lane.
- Failure Mode: copying owner scenario names into new root capture ids makes the proof rail wider without increasing validator signal.
- Pattern: when a shared main-tab tranche lands on already-covered screen captures, widen proof by adding the missing active-tab screen capture first instead of inventing a nav-only screenshot lane.
- Failure Mode: creating a synthetic top-nav proof id for chrome that is already visible on deterministic owner screens adds proof surface without adding trust.
- Pattern: when Today overview polish lands inside the already gated `today-overview-default` route, keep proof attached to that existing capture instead of inventing `today-list-*` or `today-feedback-*` screenshot ids.
- Failure Mode: splitting list rhythm or feedback-card proof away from the already deterministic Today overview screen widens the screenshot rail without increasing trust.
- Pattern: when a shared history tranche lands on history overview, sessions, exercises, or detail chrome already represented by the existing history captures, keep proof attached to those captures and only widen if a deterministic uncovered history state actually exists.
- Failure Mode: creating history-header or history-control proof ids for chrome that is already visible on deterministic history screens adds proof surface without increasing trust.
- Pattern: when a tranche lands on shared route-loading chrome, keep proof on the existing steady-state route captures unless the owner repo exposes a deterministic loading screenshot lane with a stable observation digest.
- Failure Mode: forcing screenshot gating onto delayed or animated loading overlays, particles, or boot cards weakens the proof rail by making a timing-sensitive state look deterministic.

Visual proof should only widen onto already adopted surfaces that have a deterministic screenshot route.

- Pattern: expand visual proof only when the owner repo can emit the same stable scenario artifact into both the runtime screenshot path and the approved reference lane.
- Failure Mode: opting auth-gated, install-stateful, or otherwise unstable surfaces into screenshot proof weakens the rail with flaky diffs.
- Rule: the shared main-tab pending indicator stays out of root proof until the owner repo exposes a deterministic screenshot scenario that holds that transient state without timing flake.

Curated onboarding is not opted into visual proof yet.

- The current onboarding route is auth-gated and device-stateful.
- Root proof only gates captures that already have deterministic screenshot artifacts.
- Keep curated onboarding on the semantic observer/drift lane until a stable screenshot harness exists for that family.

Entry handoff and install-gate surfaces are not opted into visual proof yet.

- The current family depends on authenticated entry resolution plus browser/PWA install capability state.
- Root proof still only gates captures that already have deterministic screenshot artifacts across browser modes.
- Keep the entry handoff family on the semantic observer/drift lane until a stable install-state screenshot harness exists.

Auth / recovery remains semantic-only for this tranche.

- The active semantic lane already covers `auth-recovery-shell`, `auth-recovery-login-screen`, `auth-recovery-signup-form`, `auth-recovery-forgot-password-form`, `auth-recovery-reset-password-form`, `auth-recovery-recovery-bridge`, `auth-recovery-message-chrome`, `auth-recovery-account-panel`, and `auth-recovery-action-chrome`.
- The family still depends on remembered-account hydration, remembered-login sync after authenticated surfaces, recovery-fragment handoff, and session establishment state that do not yet produce a stable root-side screenshot artifact and approved reference pair.
- Keep auth/recovery on the semantic observer/drift lane until one of those active capture ids has a deterministic runtime screenshot path and matching reference image.
- Pattern: if auth/recovery later becomes deterministic enough for proof, attach it to the existing active `auth-recovery-*` capture ids before inventing route-scenario, wrapper-only, `remembered-login-*`, or `login-state-*` proof ids.
- Failure Mode: forcing screenshot gating onto remembered-account or recovery-session transitions makes the proof rail flaky while pretending the wrong state is stable.

Routine editor/detail remains semantic-only for this tranche.

- Fitness does expose deterministic owner-side mobile-regression scenarios for `edit-day-default`, `edit-day-add-exercise`, and `edit-routine`.
- Root proof does not yet have approved reference images or active runtime screenshot artifacts bound to the active capture ids `edit-day-default`, `edit-routine-days-section-default`, and `edit-day-add-exercise-default`.
- The family also spans autosave and route-specific editor states, so root should not force a screenshot gate until one of those active capture ids has a stable root-side artifact path and reference image.
- Keep the routine editor/detail family on the semantic observer/drift lane until one of those active capture ids has a matching root-side screenshot binding and observation digest.
- Pattern: when owner screenshots exist for routine editor/detail routes, attach proof to the existing active editor capture ids before inventing new proof ids.
- Pattern: when the active capture map changes but the proof lane does not, refresh `expected_capture_map_digest` to the current map instead of widening the proof surface.
- Failure Mode: binding root proof to owner scenario names or stale screenshot paths instead of the active editor capture ids makes the proof rail look green while comparing the wrong surface.

Session / log-set remains semantic-only for this tranche.

- Fitness does expose deterministic owner-side mobile-regression scenarios for `active-workout-session` and `active-workout-session-expanded`.
- Root proof does not yet have approved reference images or active runtime screenshot artifacts bound to the active capture ids `exercise-log-session-header-card`, `exercise-log-entry-section`, `exercise-log-compact-row`, `exercise-log-sticky-footer`, or the shared `workout-card-disclosure-expanded` capture.
- The family also includes live timer chrome, so root should not force screenshot gating until one of those active capture ids has a frozen runtime artifact and matching reference image that stays stable across reruns.
- Keep the current session/log-set family on the semantic observer/drift lane until one of those active capture ids has a matching root-side screenshot binding and observation digest.
- Pattern: when a session/log-set tranche lands on already-covered active capture ids, reconcile proof against those capture ids first instead of inventing `active-session-*`, `session-log-*`, or owner-scenario proof ids.
- Failure Mode: binding root proof directly to owner scenario names or timer-driven screenshots without active capture-id alignment makes the proof rail look green while comparing the wrong or unstable state.

History detail / log-audit remains semantic-only for this tranche.

- The adopted family now expands into explicit semantic captures for the detail surface, edit-mode panel, field inputs, disclosure shell, and note or empty-state chrome.
- Fitness does define a deterministic owner scenario for this family as `history-detail-broken-images`, but the current repo-backed screenshot export does not materialize a root-proof artifact for the active split `history-log-*` capture ids yet.
- Root proof should only widen when a deterministic history-detail artifact exists in both the runtime screenshot path and the approved reference lane.
- Pattern: when semantic coverage replaces one broad legacy capture with several active captures, visual proof may only attach once one of those active capture ids has its own deterministic screenshot binding and matching observation digest.
- Failure Mode: binding an active `history-log-*` capture to a stale or legacy screenshot path would make the proof rail look green while comparing the wrong surface.
- Pattern: when shared history header/control polish lands inside the already proofed session and exercise routes, keep proof on `history-sessions-list-default` and `history-exercises-default` until the owner repo exposes a deterministic history-detail proof binding for an active `history-log-*` capture.
- Route loading remains visual-proof unchanged for this tranche because `RouteLoading.tsx` mounts after a route delay and uses animated glows and particles, so the steady-state Today, Routines, Settings, History sessions, and History exercises captures remain the only deterministic screenshot lane.

Chooser remains semantic-only for this tranche.

- The active semantic lane already covers `exercise-chooser-picker`, `exercise-chooser-tag-filter-control`, `exercise-chooser-search-filters`, `exercise-chooser-picker-panel`, `exercise-chooser-filter-panel`, and `exercise-chooser-goal-panel`.
- Root proof does not yet have approved reference images or active runtime screenshot artifacts bound to those capture ids, and the current chooser/search/filter states still depend on query and filter combinations that are not frozen into a deterministic root screenshot lane.
- Keep the chooser family on the semantic observer/drift lane until one of those active capture ids has a stable root-side screenshot artifact and matching reference image.
- Pattern: when a chooser tranche lands on already-covered `ExercisePicker`, `ExerciseSearchFilters`, `PickerListViewport`, and shared chooser panel or filter shell states, reconcile proof against the active `exercise-chooser-*` capture ids before inventing component-specific or shell-only proof ids.
- Failure Mode: creating `exercise-picker-*`, `exercise-search-filters-*`, `picker-list-viewport-*`, `chooser-panel-*`, or `filter-shell-*` proof ids widens the screenshot rail without increasing trust.

## Artifact Paths

By default, current screenshots are read from:

- `runtime/atlas/ui-observe/fitness/<capture-id>/visual/latest.png`

Approved reference images are read from:

- `data/atlas/ui-visual-proof/fitness/<capture-id>/reference.png`

Optional masks are read from:

- `data/atlas/ui-visual-proof/fitness/<capture-id>/mask.png`

Visual proof reports are written to:

- `runtime/atlas/ui-visual-proof/fitness/latest.json`
- `runtime/atlas/ui-visual-proof/fitness/latest.md`

Per-capture diff images are written under:

- `runtime/atlas/ui-visual-proof/fitness/<capture-id>/latest-diff.png`

## Operation

Run the proof harness from the stack root:

```powershell
python ops/atlas/ui_visual_proof/fitness.py
```

Limit to one declared capture while iterating:

```powershell
python ops/atlas/ui_visual_proof/fitness.py --capture-id today-overview-default
```

Validate wiring without writing reports or diff images:

```powershell
python ops/atlas/ui_visual_proof/fitness.py --dry-run
```

The CLI exits non-zero when any declared proof capture fails.

## Notes

- A clean semantic drift report is not enough to prove that a visual edit landed correctly.
- Visual proof should be attached to the touched capture set, not used as an unbounded screenshot vibe-check.
- If a surface changes intentionally, update the reference image or declare an allowed delta or mask explicitly instead of silently absorbing the diff.
