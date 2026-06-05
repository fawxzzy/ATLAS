# Fitness Discord Feedback Submit Picker

Date:
- 2026-05-24

Scope:
- `repos/fawxzzy-fitness`

Goal:
- refine the public feedback launcher so `Submit` matches the dismissible picker pattern already used by `Edit`
- remove the type prompt from the create modal
- let bug and feature cards preserve explicit section text instead of collapsing back to generic forum prose

What changed:
- the feedback launcher buttons now read `Submit` and `Edit`
- the launcher copy is shorter and flow-oriented
- `Submit` now opens an ephemeral type picker with:
  - `Bug` / `Feature` dropdown
  - type-aware `Create Bug` / `Create Feature` button
  - cancel action
- create and edit modals now use type-specific section guidance instead of a top `Type` field
- bug and feature cards can now store explicit section overrides in bounded structured form:
  - bug: `Expected behavior`, `Actual behavior`, `Steps to reproduce`, `Acceptance Criteria`
  - feature: `User Story`, `Acceptance Criteria`
- forum rendering now prefers stored section overrides and only falls back to deterministic generated copy when an explicit override was not supplied

Files:
- `repos/fawxzzy-fitness/src/lib/discord/interactions.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions.test.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions-route.test.ts`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.test.ts`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`

Verification:
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions.test.ts`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/bug-reports.test.ts`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `npm run verify`
- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

Notes:
- unrelated preexisting Fitness residue in asset/build files was left untouched
- no deploy, Discord mutation, or Supabase mutation was performed in this package
