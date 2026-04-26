# 2026-04-26 Fitness Product And Catalog Log

## Scope

Cross-pass ATLAS note for the `repos/fawxzzy-fitness` and `repos/fawxzzy-trove` work completed in this session.

## Product Work Recorded

- Reduced login-route blocking by moving signed-in redirect behavior off the first `/login` paint.
- Tightened install/login gating so copy-link only appears in the relevant in-app-browser flow.
- Fixed auth-shell caret leakage in shared login/install surfaces.
- Improved installed-app update behavior with proactive service-worker/version checks and background apply behavior.
- Corrected iOS standalone shell issues around bottom safe-area color and phantom bottom spacing.
- Adjusted Trove-to-Fitness iOS handoff behavior to avoid broken cross-origin standalone navigation.
- Added a reference-only Stretch hub pattern so one top-level `Stretch` card can fan into a sub-library of guided drills inside exercise info and current-session UI without polluting normal logging/history flows.
- Added a concentrated Stretch surface pass across history/browser cards, add-exercise picker language, workout-day planning rows, today cards, and current-session/live-reference mode.
- Standardized the Stretch info-screen drill list toward the same card/list language used by the add-exercise chooser so the hub reads like a native part of the product instead of a one-off panel.
- Tightened the Stretch contract so card surfaces stay tag-first (`Mobility`, `Recovery`, `Bodyweight`), suppress normal goal/description noise, and keep QA rooted in signed-in localhost captures rather than preview-only routes.
- Refined Stretch add-exercise behavior so the real configure-goal surface is visually `sets`-only instead of showing empty generic measurement scaffolding.
- Locked the Stretch info/live-reference copy to the canonical guide language (`Collection of stretches...`) instead of allowing stale DB `how_to_short` text to leak back into the hub surfaces.
- Extended the local CDP screenshot harness with a `fullPage` flag and kept using signed-in localhost captures as the source of truth for live mobile UI review.
- Tightened the Stretch sub-card presentation again by removing the left visual strip and using an inline green divider below the title/meta block before the descriptive copy.
- Propagated that same detailed-card treatment into the history family by switching boxed top-right meta tags to plain green text and adding the same thin gradient divider between heading/meta content and lower detail blocks.
- Added a stretch-specific search and horizontal area-filter rail directly inside the bounded Stretch library viewport so the hub keeps the same scroll-shell behavior as add-exercise while staying curated to mobility content.
- Cleaned the Stretch library shell further by centering the library heading, adding an explicit drill count, simplifying the sticky refinement header, and exposing a clear action so the library reads as one polished module instead of stacked utility controls.

## Catalog Work Recorded

- Added filter-only exercise curation tags while keeping cards limited to the main three taxonomy chips.
- Standardized history filter behavior to support many tag categories without losing per-category horizontal browsing.
- Generated canonical curation tags and professionalized `how_to_short` copy from the source catalog.
- Added explicit `measurement_type` and `default_unit` coverage across the full exercise catalog.
- Added second-layer taxonomy for `plane_of_motion`, `exercise_utility`, and `body_position`.
- Added analysis outputs, a review queue, and CSV/JSON index artifacts for future scale-up passes.
- Captured the next blueprint direction: expand the main exercise library by meaningful taxonomy-coverage gaps and treat the stretch library as a parallel full-body codex with its own coverage requirements.

## Process Notes

- ATLAS should remain the durable place for reusable workflow notes and audit history.
- Repo-local docs should carry analysis artifacts that are specific to the application dataset.
- Future catalog-expansion passes should start from the playbook:
  `docs/playbooks/fitness-exercise-catalog-ops.md`

## Follow-Up Focus

1. Visual-review the non-`reps` catalog rows and rare-equipment rows before adding new exercises.
2. Decide whether runtime payloads should split lightweight browse metadata from long-form exercise detail payloads.
3. Lock a long-term slug/id strategy before large catalog expansion.
4. Reuse the Stretch hub pattern for other reference-only entities only when they do not belong in the normal log/history model.
5. Expand future exercise additions by taxonomy-combination coverage, not just raw count, and keep stretch-library coverage tracked as its own full-body codex lane.
