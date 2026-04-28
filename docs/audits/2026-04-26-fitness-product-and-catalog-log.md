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
- Expanded the Stretch hub from a short starter list into a broader full-body basic/intermediate codex, widened the tray back toward the intended `~2.5 cards visible` behavior, removed the redundant `guided drills` subtitle, and kept the search/filter controls outside the scroll viewport so the tray remains card-first.

## Catalog Work Recorded

- Added filter-only exercise curation tags while keeping cards limited to the main three taxonomy chips.
- Standardized history filter behavior to support many tag categories without losing per-category horizontal browsing.
- Generated canonical curation tags and professionalized `how_to_short` copy from the source catalog.
- Added explicit `measurement_type` and `default_unit` coverage across the full exercise catalog.
- Added second-layer taxonomy for `plane_of_motion`, `exercise_utility`, and `body_position`.
- Added analysis outputs, a review queue, and CSV/JSON index artifacts for future scale-up passes.
- Captured the next blueprint direction: expand the main exercise library by meaningful taxonomy-coverage gaps and treat the stretch library as a parallel full-body codex with its own coverage requirements.
- Grounded the stretch-codex expansion in public exercise-reference guidance from ACE, NASM, ExRx, and Harvard Health, then rewrote the in-app entries into the product's shorter professional cue style rather than copying source text directly.
- Expanded the stretch codex further to `50` home/gym-friendly entries, adding broader chest, biceps, adductor, hamstring, front-body, foot, and dynamic mobility coverage while keeping the same lightweight in-app data shape.
- Added a generic mobility/recovery fallback description in the exercise info layer so custom rows like `Mobility` no longer render blank explanation copy even when they are not part of the canonical catalog.
- Expanded the stretch codex again to `62` home/gym-friendly entries, filling lateral-hip, QL/side-body, rhomboid, serratus, straddle, dynamic adductor, and additional low-back/hip reset gaps.
- Tightened stretch-library scaling so the UI now filters against a precomputed summary index, resolves full drill detail by `id`, and progressively renders the bounded tray instead of dropping the entire codex into the DOM at once.
- Expanded the stretch codex again to `76` entries, adding puppy pose, thread-the-needle, triceps-bench, shoulder external rotation, strap extension, straddle-side reach, hip internal rotation, 90/90 flow, shin/top-of-foot, toe extension, SCM, pronation, supination, and IT-band line coverage.
- Split the Stretch hub runtime into summary and deferred-detail files, added a generator script (`npm run gen:stretch-library-split`), and switched the panel to load long-form stretch cues/how-to copy after the lightweight shell instead of on the first client path.
- Expanded the stretch codex again to `88` entries, adding wall angel, windmill, deep squat pry, adductor glide, rear-delt doorway, reverse prayer, seated calf strap, ankle inversion/eversion, banana stretch, scorpion rotation, foam-roll chest opener, and groiner coverage.
- Wired stretch split generation into `prebuild` so the lightweight summary path and deferred detail path regenerate automatically during normal build flow instead of relying on manual discipline.
- Expanded the stretch codex to `100` entries, adding sleeper, heel-on-box hamstring, doorway lat hang, lizard lunge, pigeon, shin-box fold, cat-tail side bend, toe yoga, supported wall split calf, bench-supported pec/biceps opener, bench-supported calf/ankle rock, and another supine figure-four variant.
- Tightened the stretch query path again by precomputing per-filter candidate buckets and using tokenized query matching so the UI can narrow into a smaller working set before scanning text.
- Standardized the add-exercise goal measurement inputs onto a single inline-label contract: green meta text in the top-right of every field, with matching input padding so sets, reps, weight, time, distance, calories, and RPE no longer mix placeholder-only, centered-right, and bottom-right label treatments.
- Standardized preview-time grammar across the workout-builder/session-target surfaces so any previewed duration metric now renders with an explicit `s` suffix (`3:00 s`) instead of relying on bare clock text.
- Promoted the green top-right measurement-label treatment from add-exercise-only to the shared `MeasurementPanelV2` contract so live logging, edit-day measurement editing, and other real measurement-entry surfaces all use the same label placement and input padding rules.
- Replaced raw text bullets in goal/metric preview surfaces with structured green-dot separators so add-exercise goal previews, inline goal summaries, and live session metric previews now share the same visual grammar instead of faking separators inside a single text string.
- Tightened the mobile auth/input contract across the pre-login surfaces by reducing auth field height/padding on phone widths, trimming auth-form stack spacing, and moving signup/forgot/reset onto the same shared auth input class as login so those screens stop mixing oversized generic inputs with the login-specific chrome.
- Hardened the exercise-filter taxonomy path by parsing stringified `curation_tags`, backfilling canonical curation tags from the repo catalog when DB rows omit them, and wiring the add-exercise picker onto the same expanded curation-group filter model as history so filter surfaces stop silently collapsing back to the legacy three-group view.

## Process Notes

- ATLAS should remain the durable place for reusable workflow notes and audit history.
- Repo-local docs should carry analysis artifacts that are specific to the application dataset.
- Future catalog-expansion passes should start from the playbook:
  `docs/playbooks/fitness-exercise-catalog-ops.md`

## Follow-Up Focus

1. Visual-review the non-`reps` catalog rows and rare-equipment rows before adding new exercises.
2. Decide when the stretch codex should graduate from client-side summary/detail indexing to a true split payload boundary.
3. Lock a long-term slug/id strategy before large catalog expansion.
4. Reuse the Stretch hub pattern for other reference-only entities only when they do not belong in the normal log/history model.
5. Expand future exercise additions by taxonomy-combination coverage, not just raw count, and keep stretch-library coverage tracked as its own full-body codex lane.
