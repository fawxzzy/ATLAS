# Fitness Exercise Catalog Ops

## Purpose

Reusable ATLAS-level workflow for evolving the `fawxzzy-fitness` exercise catalog without letting taxonomy, migrations, or runtime usage drift apart.

## Source Of Truth

- Repo: `repos/fawxzzy-fitness`
- Canonical catalog: `repos/fawxzzy-fitness/supabase/data/global_exercises_canonical.json`
- Catalog refresh generator: `repos/fawxzzy-fitness/scripts/refresh-exercise-catalog.mjs`
- Catalog analysis generator: `repos/fawxzzy-fitness/scripts/analyze-exercise-catalog.mjs`

## Required Outputs

- DB migration derived from canonical catalog:
  `repos/fawxzzy-fitness/supabase/migrations/040_exercise_curation_tags_and_howto_refresh.sql`
- Analysis bundle:
  `repos/fawxzzy-fitness/supabase/data/global_exercises_catalog_index.json`
  `repos/fawxzzy-fitness/supabase/data/global_exercises_catalog_index.csv`
  `repos/fawxzzy-fitness/supabase/data/global_exercises_review_queue.json`
- Human-readable review docs:
  `repos/fawxzzy-fitness/docs/exercise-catalog-analysis.md`
  `repos/fawxzzy-fitness/docs/exercise-catalog-review-queue.md`

## Workflow

1. Edit or regenerate the canonical catalog, not UI fixtures or ad hoc DB rows.
2. Run `node scripts/refresh-exercise-catalog.mjs` in `repos/fawxzzy-fitness`.
3. Run `npm run analyze:exercise-catalog` in `repos/fawxzzy-fitness`.
4. Review:
   `docs/exercise-catalog-analysis.md`
   `docs/exercise-catalog-review-queue.md`
   `supabase/data/global_exercises_catalog_index.csv`
5. If metadata contracts changed, inspect the generated migration before deploy.
6. Run repo verification:
   `npm run verify`
   `npm run build`
7. Record the pass in an ATLAS audit note under `docs/audits/`.

## Operating Rules

- Keep canonical equipment values normalized and finite.
- Prefer deterministic generators over hand-editing 100+ rows.
- Treat `measurement_type` and `default_unit` as explicit catalog contract fields, not runtime fallback assumptions.
- Keep filter-only taxonomy separate from card-display taxonomy.
- Expand the library by coverage, not by raw count alone. New exercises should fill meaningful gaps in:
  `primary_muscle`
  `movement_pattern` / `pattern_detail`
  `equipment`
  `training_goal`
- Current filter/logic taxonomy includes:
  `pattern_detail`, `plane_of_motion`, `exercise_utility`, `body_position`, `training_goal`, `difficulty`, `setup_cost`, `stability_requirement`, `unilateral_profile`, `loading_profile`, `joint_emphasis`, `spine_demand`, `grip_constraint`
- Use ATLAS docs for reusable process notes; use repo docs for app-specific analysis artifacts.
- When a concept belongs in browse/reference but not in normal performance logging, model it as a reference-only hub entity backed by its own dataset rather than forcing it into the main exercise logging contract.

## Coverage Matrix

- Before large catalog expansion, audit which high-value tag combinations already exist and which are thin or missing.
- Distinguish between:
  exercise coverage for the workout engine
  stretch coverage for the mobility/reference codex
- Similar-looking exercises are still acceptable when they create a reasoned programming difference such as:
  equipment constraint
  stability demand
  unilateral vs bilateral loading
  setup cost
  spine demand
  tension or joint emphasis differences
- The goal is not "no overlap"; the goal is overlap with a defensible reason the engine can use.

## Reference-Only Hubs

- Current example: the single `Stretch` card in `fawxzzy-fitness`.
- Keep the top-level catalog surface to one hub card when the sub-items would create noise in browse, history, or stats.
- Store the hub's sub-items in a separate typed dataset so the library can expand without inflating the main exercise table.
- Reuse one presentation component across:
  `exercise info`
  `current-session reference mode`
- For visual QA, review the hub in the same system contexts the user actually touches:
  `add-exercise picker row`
  `history/browser compact + detailed cards`
  `planned-day row treatment`
  `today card`
  `current-session/live-reference mode`
  `full exercise info screen`
- Prefer live authenticated localhost captures for these QA passes over custom demo routes when the goal is to validate real account data, logging state, and route wiring.
- Style hub sub-item lists to inherit the app's existing chooser/list language whenever possible so the reference layer feels native instead of bolted on.
- For the Stretch hub specifically:
  keep card surfaces free of normal goal/description copy
  use `Mobility`, `Recovery`, and an optional third identity chip (`Bodyweight` currently)
  treat add-exercise configuration as `sets`-only unless the product later decides Stretch should become a true logged modality
- When validating real UI changes for these hubs, prefer live localhost captures from a signed-in QA account over preview routes.
  On `fawxzzy-fitness`, the current reliable path is a localhost-only `x-atlas-access-token` header fallback plus short-lived fresh dev servers per capture.
- Do not show normal set logging, PRs, or history for reference-only hubs unless the product explicitly decides they should become first-class log entities later.
- Apply the same coverage thinking here: the stretch library should cover the full body/physique map with targeted options, but it remains a separate codex from the logged exercise engine.
- Keep stretch-library controls outside the bounded card tray when the goal is to preserve a clean `2-3 cards visible` viewport. Search and filter can sit above the tray, but the tray itself should stay focused on card scanning and vertical browsing.
- As the stretch codex grows, keep the tray cheap by:
  precomputing search/filter summaries once
  resolving full detail payloads by `id`
  progressively rendering only the visible card batch inside the bounded tray
  using CSS containment/content-visibility on individual library cards when appropriate
  precomputing filter buckets so narrow category rails query a smaller candidate pool instead of rescanning the full summary list
- Keep a deterministic split-generation step for the Stretch hub so runtime files do not drift:
  source authoring currently lives in `repos/fawxzzy-fitness/src/lib/stretch-library.ts`
  generate browse summaries with `npm run gen:stretch-library-split`
  consume `stretch-library-summaries.ts` on the initial client path
  defer `stretch-library-details.ts` behind the library panel so long-form cues/how-to copy load after the shell
  keep `npm run build` / `prebuild` responsible for regenerating the split so source edits cannot ship stale summary/detail artifacts
- If the codex grows far beyond the current client-friendly range, split lightweight browse metadata from long-form drill detail payloads before inflating the main app bundle.
- When expanding the Stretch hub, add coverage by body-region gaps first:
  hips and hip flexors
  glutes and hip rotation
  hamstrings
  adductors and groin
  quads
  calves and ankles
  chest
  shoulders and triceps
  upper back and thoracic rotation
  neck and forearms
  lateral hip / TFL / glute med
  side body / QL / ribcage reach
  serratus / scapular reach
  feet / arches / toes / peroneals
- Prefer reputable movement-reference sources for stretch-codex additions, then rewrite the entry data into the app's shorter professional voice.
  Current anchors used for the first codex pass:
  [ACE exercise library](https://www.acefitness.org/resources/everyone/exercise-library/)
  [NASM stretch and exercise library](https://www.nasm.org/resource-center/exercise-library/)
  [ExRx stretch directory](https://exrx.net/Lists/Directory)
  [Harvard Health stretching guidance](https://www.health.harvard.edu/exercise-and-fitness/take-time-to-stretch-FV8ERJTB)
- Recent high-value gap fills added on top of the first codex wave:
  lateral hip / TFL / IT-band line
  rhomboid / serratus / scapular reach
  deep hip rotation
  straddle and side-body combinations
  front-neck / SCM
  pronation / supination forearm work
  top-of-foot / shin / toe extension
  deep squat and groiner prep
  windmill / scorpion rotational flows
  wall angel and foam-roll chest opening
  sleeper / shoulder-rotation work
  lizard / pigeon / shin-box hip-opening variants
  heel-on-box and support-assisted hamstring/calf progressions

## Visual Review Order

1. Non-`reps` measurement rows.
2. Rare equipment rows (`Plate`, `Sled`, `Smith Machine`, `Cardio Machine`).
3. Any review-queue flags generated by `analyze-exercise-catalog`.
4. New exercises before they are merged into the main canonical list.
