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

## First Opted Captures

The currently proof-gated captures are:

- `settings-overview-default`
- `today-overview-default`
- `history-sessions-list-default`
- `workout-card-session-summary-card`

All four are currently baselined as `unchanged`.

- `settings-overview-default` is the stable control surface.
- `today-overview-default` is the first high-signal Today surface tied to the active adoption rail.
- `history-sessions-list-default` extends the proof lane into the history session-summary family.
- `workout-card-session-summary-card` extends the proof lane into the workout-card/session-summary family.

The approved references are seeded from the repo's existing deterministic mobile-regression flow at `393px`, then copied into the root-owned proof locations.

- `settings-overview-default` maps to the `settings-default` mobile-regression scenario.
- `today-overview-default` maps to the `today-default` mobile-regression scenario.
- `history-sessions-list-default` maps to the `history-sessions-compact` mobile-regression scenario.
- `workout-card-session-summary-card` maps to the `today-in-session-summary` mobile-regression scenario.

Curated onboarding is not opted into visual proof yet.

- The current onboarding route is auth-gated and device-stateful.
- Root proof only gates captures that already have deterministic screenshot artifacts.
- Keep curated onboarding on the semantic observer/drift lane until a stable screenshot harness exists for that family.

Entry handoff and install-gate surfaces are not opted into visual proof yet.

- The current family depends on authenticated entry resolution plus browser/PWA install capability state.
- Root proof still only gates captures that already have deterministic screenshot artifacts across browser modes.
- Keep the entry handoff family on the semantic observer/drift lane until a stable install-state screenshot harness exists.

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
python ops/atlas/ui_visual_proof/fitness.py --capture-id auth-recovery-login-screen
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
