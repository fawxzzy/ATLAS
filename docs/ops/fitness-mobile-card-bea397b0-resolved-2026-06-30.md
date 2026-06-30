# Fitness Mobile Card bea397b0 Resolved - 2026-06-30

## Status

`Run a mobile UI normalization pass across every Fitness screen` is ready for closeout.

The remaining work that used to keep this lane open is now proof-backed and resolved:

- the routines duplicate/create mobile chooser surfaces were re-normalized
- the duplicate routine modal hydration mismatch in `CreateRoutineClient` was fixed
- the mobile regression capture pack was rebuilt against the real local QA lane on `http://127.0.0.1:3002`
- the board set was rebuilt from the refreshed manifest and screenshots

## Card-Update

Closed out the Fitness mobile normalization card after the final routines-family audit and proof rebuild.

What landed in the final pass:

- fixed the duplicate routine modal hydration mismatch that was surfacing as the red `3 errors` toast on the mobile regression route
- normalized the routine duplicate chooser metric lane to the same mobile horizontal-scroll contract already used by the workout-plan duplicate chooser
- refreshed the full `57` scenario mobile-regression capture pack against `http://127.0.0.1:3002`
- rebuilt the named mobile board artifacts from the refreshed manifest
- re-ran the deterministic fixture suite and kept `108/108` tests green

Closeout proof:

- feature card id: `bea397b0`
- forum thread id: `1521542046329077932`
- closing status: `resolved`
- repo branch: `main`
- repo head: `48453c915b17f13a24898f50ebdfd79e581c2174`
- mobile-regression fixture tests: `108/108`
- mobile regression scenario count: `57`
- mobile regression manifest: `repos/fawxzzy-fitness/.codex/qa/mobile-regression/manifest.json`
- mobile regression manifest base url: `http://127.0.0.1:3002`
- board proofs:
  - `repos/fawxzzy-fitness/.codex/qa/mobile-regression/exercise-cards-board.png`
  - `repos/fawxzzy-fitness/.codex/qa/mobile-regression/session-logging-board.png`
  - `repos/fawxzzy-fitness/.codex/qa/mobile-regression/session-summaries-board.png`
  - `repos/fawxzzy-fitness/.codex/qa/mobile-regression/settings-detail-board.png`
  - `repos/fawxzzy-fitness/.codex/qa/mobile-regression/mega-board.png`
- targeted Playwright probe on `routines-list-create-duplicate` after the hydration fix:
  - page status: `200`
  - console errors: `0`
  - page errors: `0`

Current state:

- no known remaining mobile regression blocker is open on the routines duplicate/create surfaces
- remaining future work is subjective polish, not unresolved correctness or layout drift

<!-- discordos-update-post-receipt:start -->
## Discord Publication

- status: `sent`
- sends messages: `true`
- Discord HTTP status: `200`
- channel id: `1504671871512346695`
- message id: `1521627443968999597`
- timestamp: `2026-06-30T21:24:13.113000+00:00`
- mentions disabled: `true`
<!-- discordos-update-post-receipt:end -->
