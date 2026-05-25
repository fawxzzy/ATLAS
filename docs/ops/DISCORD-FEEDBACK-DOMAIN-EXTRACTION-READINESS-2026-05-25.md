# DiscordOS Feedback Domain Extraction Readiness Gate - 2026-05-25

## Scope

- Lane: Discord OS Infrastructure Separation
- Mode: docs-only readiness gate
- No code movement
- No Supabase mutation
- No Vercel mutation
- No Discord mutation
- No env pull or secret output

## Goal

Decide whether the Fitness-isolated feedback runtime boundary is ready to become the first DiscordOS extraction slice, and if so, what the first implementation package should actually be.

## Inputs

- `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
- `docs/ops/DISCORD-ROUTE-DECOMPOSITION-PACKAGE-1-2026-05-25.md`
- `docs/ops/DISCORD-RUNTIME-UTILITY-EXTRACTION-PACKAGE-1-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/DISCORD-OS-SUPABASE-SCHEMA-LANDING-PLAN-2026-05-24.md`
- `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/**`
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- `repos/fawxzzy-fitness/src/lib/env.ts`
- `repos/DiscordOS/**`

## Gate Decision

Decision: **conditionally ready**

Meaning:

- the Fitness-owned feedback runtime boundary is now clean enough to justify a first DiscordOS-facing extraction lane
- it is **not** ready for direct code copy or runtime cutover
- the next safe implementation is **contract/interface scaffolding only** in `repos/DiscordOS`

This gate does **not** approve:

- copying the Fitness feedback runtime into `repos/DiscordOS`
- moving `discord_feedback_reports`
- changing the live interaction route
- changing the live worker target
- changing current env ownership

## 1. Extraction Candidates

### Ready-later candidates after contract scaffolding

These are the modules with the best future DiscordOS fit:

- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`
  - pure lifecycle/status/value helpers
  - no direct Supabase access
  - no direct env dependency
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
  - good structural extraction candidate
  - already dependency-injected for Discord side effects and forum-state persistence
  - still depends on Fitness-owned report row shape and Fitness forum-state recording callbacks

### Candidate-adjacent supporting surfaces

- selected formatting and forum-card builders in `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- selected feedback emoji helpers in `repos/fawxzzy-fitness/src/lib/discord/feedback-emojis.ts`

These should not be copied first. They should be wrapped behind contract shapes first so DiscordOS does not inherit Fitness internals wholesale.

## 2. Modules That Must Stay Fitness-Owned For Now

These must remain Fitness-owned at this stage:

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
  - still the live public entrypoint
- `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
  - still owns live persistence and report-row shape for `discord_feedback_reports`
- `repos/fawxzzy-fitness/src/lib/discord/member-links.ts`
  - still bridges Fitness identity and Discord identity
- Fitness verification issuance and profile/account surfaces
- current live worker target and runtime host assumptions

Reason:

- the extracted feedback boundary is cleaner, but the canonical writer, canonical runtime, and canonical data host are all still Fitness

## 3. Current Data Dependencies

The isolated feedback boundary still depends on Fitness-owned data and callbacks for:

- feedback report persistence
- feedback report lookup by report id or prefix
- feedback report forum-state recording
- reporter identity fields already hydrated onto the report row
- permission checks that still depend on the current Discord interaction/runtime posture
- thread/message ids already written into current Fitness rows

Implication:

- the boundary is extraction-shaped, but not yet source-of-truth independent

## 4. Supabase Tables Touched

Current directly relevant tables and seams:

- `discord_feedback_reports`
  - core feedback runtime state
- `discord_member_links`
  - reporter identity bridge and member-number context

Current indirectly relevant retained Fitness truth:

- `profiles`
  - member-number and Fitness identity context
- verification/token/account surfaces
  - not part of this feedback slice, but still part of the broader seam boundary

## 5. DiscordOS Schema / Contracts Required First

Before real extraction, DiscordOS needs explicit contracts or schema plans for:

- feedback report runtime record shape
- feedback forum-state record shape
- feedback audit-comment contract
- immutable feedback report id continuity
- reporter identity contract
  - Discord user id
  - optional Fitness user reference
  - optional member-number display context
- Fitness-to-DiscordOS lookup/result codes for:
  - report lookup
  - ambiguity
  - missing report
  - persistence/update failure

Minimum first contract set:

1. `FeedbackReportSummary`
2. `FeedbackForumState`
3. `FeedbackAuditEvent`
4. `FeedbackLookupResult`
5. `FeedbackThreadSyncPort`
6. `FeedbackReportStorePort`

## 6. Env / Secret Classes Needed Later

Future DiscordOS extraction of feedback would later need DiscordOS-owned runtime env classes for:

- Discord bot token
- Discord application id
- Discord guild/channel/forum ids relevant to feedback
- Discord feedback emoji ids if they remain runtime-configured
- DiscordOS Supabase keys

What must not move yet:

- Fitness auth/profile env
- verification issuance secrets
- any mixed env bundle copied out of `src/lib/env.ts`

Rule:

- the next package should declare env interfaces, not move env values

## 7. Tests That Prove Behavior Before Extraction

Current proof set already available in Fitness:

- `npm run typecheck`
- `npm run sanity:quick`
- `npm run build`
- `src/lib/discord/runtime/helpers.test.ts`
- `src/lib/discord/runtime/route-domains.test.ts`
- `src/lib/discord/interactions-route.test.ts`
- `src/lib/discord/runtime/feedback/helpers.test.ts`
- `src/lib/discord/bug-reports.test.ts`
- `src/lib/discord/feedback-emojis.test.ts`

These currently prove:

- route entry remains stable
- feedback helper semantics are stable
- feedback forum/report formatting still behaves as expected
- feedback-related interaction flows still pass against the current Fitness host

## 8. Tests Needed To Prove Behavior After Extraction

The first DiscordOS-facing extraction lane should add tests for:

- contract-shape compatibility between Fitness report rows and DiscordOS feedback interfaces
- forum sync adapter behavior through ports, not direct Fitness imports
- audit-comment adapter behavior through ports
- lookup-result and failure-code normalization across the seam

Once real code starts landing in `repos/DiscordOS`, the proof set should include:

- DiscordOS-local unit tests for feedback contracts/interfaces
- fixture-based parity tests comparing Fitness feedback helper outputs against DiscordOS adapter expectations
- later read-only integration proof against the future DiscordOS schema shape

## 9. Rollback Posture

Rollback is currently straightforward because no move has happened yet:

- keep Fitness as canonical runtime and canonical writer
- do not switch worker target
- do not dual-write feedback state
- if DiscordOS contract scaffolding proves wrong, discard or revise the scaffold without touching live behavior

This is exactly why the first implementation should be a scaffold, not a migration.

## 10. First Safe Implementation Choice

Decision:

- **create contract interfaces only**

Not approved as first move:

- copy shared pure utilities into DiscordOS
- dual-read proof
- full feedback code copy
- row movement

Reason:

- pure helper copy would be premature without first freezing the contract that those helpers are supposed to serve
- dual-read proof is too early because the DiscordOS feedback schema is still not landed
- direct code copy would drag Fitness-owned row shapes and persistence assumptions into the new repo

## Readiness Matrix

| Question | Answer |
| --- | --- |
| Is feedback the best first real domain slice? | Yes |
| Is the isolated Fitness boundary materially cleaner than before? | Yes |
| Is the live route still Fitness-owned? | Yes |
| Is DiscordOS feedback schema landed? | No |
| Are feedback contracts explicit enough to start a scaffold? | Yes |
| Is direct code copy into `repos/DiscordOS` safe now? | No |
| Is data migration safe now? | No |
| Is runtime cutover safe now? | No |

## Recommended Next Package

Next package:

- `DiscordOS Feedback Contract Scaffold Package 1`

Scope should be limited to `repos/DiscordOS` and should create only:

- feedback domain interface types
- adapter/port contracts
- placeholder docs for Fitness-owned upstream inputs
- no copied runtime logic
- no Supabase schema
- no env values

## Explicit No-Go Conclusions

Do not do any of these yet:

- copy `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts` into DiscordOS
- copy `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts` into DiscordOS
- move `discord_feedback_reports`
- point the gateway worker at DiscordOS
- introduce DiscordOS as a live responder

## Result

The gate concludes that the feedback runtime boundary is **ready for a contract/interface scaffold** in `repos/DiscordOS`, but **not ready for runtime code copy or live ownership transfer**.
