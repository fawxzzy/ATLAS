# DiscordOS Feedback Permission Adapter-Consumer Planning Package 3 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback permission adapter-consumer planning package 3`
- Mode: `docs-only seam planning`
- Control-plane checkpoint: `main@8a5ec9b`

## Scope

Plan exactly one named DiscordOS feedback adapter-consumer seam after:

- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`

Chosen port:

- `FeedbackPermissionPort`

In scope:

- one named feedback port surface
- its producer/source surface
- its future consumer surface
- its contract shape and ownership boundary

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- permission-truth ownership transfer
- worker retarget
- Vercel cutover
- dual-read implementation
- preview/unfurl gate reopening
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`

## Operating Posture

- ATLAS root remains the coordination and receipt layer
- this pass is planning only
- the packet stays tied to one named feedback port
- the seam stays policy-bounded and non-activating
- no owner-repo tracked content is changed
- Fitness remains the canonical permission-enforcement owner for live feedback flows
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@8a5ec9be2340e86ff2bfd36f130f823ff2eaf198`
- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/PREVIEW-UNFURL-AND-DISCORDOS-FOLLOW-ON-QUEUE-REASSESSMENT-2026-05-26.md`
- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`

## Chosen Port

Selected third port:

- `FeedbackPermissionPort`

Current contract shape:

```ts
interface FeedbackPermissionPort {
  canAccessAnyFeedbackReport(permissions: string | null): boolean;
}
```

## Why This Port Was Chosen

`FeedbackPermissionPort` is the right third seam because:

- package 1 already isolates report identity lookup
- package 2 already isolates bounded reference and lifecycle reads
- the next smallest useful seam is the broad staff-access decision currently used to decide whether a caller may act across reports they did not submit
- the current Fitness helper already exposes this decision through a narrow wrapper without requiring direct report-row access

Why it stays small enough:

- it scopes only the cross-report staff-access decision
- it does not attempt to model every feedback action or every Discord permission class
- it does not require schema landing, forum-side effects, or runtime activation
- it composes with the already-planned lookup and report-store seams instead of replacing them

Why it is not a full policy engine seam:

- the live route still combines staff access with reporter ownership and report-status checks
- those row-local checks still depend on Fitness-owned lookup/store truth
- broadening this port into a full authorization system here would collapse read-side planning into policy ownership transfer

## Producer / Source Surface

Current Fitness-owned producer side:

- `discordMemberHasBugStatusPermission(...)` in `repos/fawxzzy-fitness/src/lib/discord/interactions.ts`
- `canAccessAnyFeedbackReport(...)` wrapper in `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`
- live composition call sites in `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`

Current live rule being wrapped:

- broad feedback staff access is granted when the member permission bitfield includes:
  - `ADMINISTRATOR`
  - `MANAGE_GUILD`
  - `MANAGE_THREADS`
  - `MANAGE_MESSAGES`

What stays Fitness-owned:

- permission-bit parsing and live Discord permission semantics
- any future changes to the broad staff-access rule
- the composition between:
  - caller permission bitfield
  - reporter ownership on the report row
  - status-based restrictions on update/withdraw flows
- live interaction-route enforcement

## Consumer Surface

First future consumer class for this seam:

- DiscordOS feedback consumers that need to know whether the caller has broad staff access across reports before composing that answer with lookup/store results

Consumer examples the seam should eventually support:

- manage-card flows that allow staff to access reports they did not submit
- update/withdraw targeting flows that distinguish:
  - reporter-owned actions
  - broader staff actions
- future thread-sync or audit consumers that should branch on staff access without importing Fitness permission helpers directly

Current rule:

- this packet plans the permission boundary only
- it does not implement a DiscordOS permission adapter or route-level policy handler

## Contract Boundary

### Input

- `permissions: string | null`

Meaning:

- the input is the caller’s current Discord member permission bitfield as already surfaced to the live Fitness route

### Output

- `boolean`

Normalized outcomes for the first seam:

- `true`
  - the caller has broad staff access and may access feedback beyond reporter-owned scope
- `false`
  - the caller does not have broad staff access
  - malformed, missing, or unusable permission values also normalize to `false` to preserve current Fitness behavior

Important rule:

- this first permission seam intentionally does not introduce a richer failure object
- `PERMISSION_DENIED` remains a downstream consumer or response outcome, not the direct return type of this narrow helper seam

Why this boundary is intentionally minimal:

- it mirrors the current code-facing stub in `repos/DiscordOS/src/contracts/feedback.ts`
- it avoids widening the seam into a generic authorization framework before the runtime owner is even moving

## Ownership Boundary

### Fitness keeps

- canonical interpretation of the current Discord permission bitfield
- the live broad-staff gate for feedback actions
- reporter-ownership checks that still compose with `reporterDiscordUserId`
- status-based action restrictions
- live response wording and route-level denial behavior

### DiscordOS later receives

- a narrow policy-facing seam for broad staff-access checks
- no ownership of the underlying permission truth
- no authority to redefine report-specific permission semantics in this package

Boundary rule:

- `FeedbackPermissionPort` is a staff-access decision seam, not a transfer of permission-policy ownership

## Composition With Earlier Seams

Planned future composition:

1. `FeedbackLookupPort`
   - resolves the target report identity
2. `FeedbackReportStorePort`
   - provides reporter reference and lifecycle projections
3. `FeedbackPermissionPort`
   - answers whether the caller has broad staff access
4. a future DiscordOS consumer composes those results to decide whether to:
   - allow a staff action
   - fall back to reporter-owned access checks
   - deny the operation

Why composition matters:

- the permission seam alone does not answer report-specific authorization
- it only answers the broad “is this caller staff for feedback management” question
- row-local authorization remains downstream and depends on lookup/store outputs

## Data Flow

Planned future flow:

1. a DiscordOS feedback consumer receives the caller permission bitfield
2. the consumer calls `FeedbackPermissionPort.canAccessAnyFeedbackReport(permissions)`
3. the Fitness-owned adapter evaluates the current broad staff-access rule
4. the adapter returns:
   - `true` for broad staff access, or
   - `false` for non-staff or unusable permission values
5. the DiscordOS consumer combines that answer with lookup/store results before deciding whether to continue a later action flow

## Explicit Non-Goals

This package does not plan or approve:

- a full action-by-action authorization matrix
- direct DiscordOS interpretation of raw Discord permission bitfields
- report-row ownership transfer
- lifecycle/status write approval through DiscordOS
- reporter identity ownership transfer
- schema landing
- dual-read proof
- worker retarget
- runtime activation

Why reporter ownership stays out of this seam:

- reporter checks still depend on Fitness-owned report reference data
- package 2 already bounded that row-local reference surface behind `FeedbackReportStorePort`
- moving reporter ownership logic into this port would blur policy and row-truth boundaries

## Allowed Future Follow-On Packages

Allowed next tiny planning packets after this one:

1. `DiscordOS feedback thread-sync adapter-consumer planning package 4`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Why `FeedbackThreadSyncPort` is the clearest next packet:

- the read-side lookup/store seams are now defined
- the broad staff-access gate is now defined
- the next smallest remaining boundary is the side-effecting thread-sync seam, which can now be planned against stable lookup/store/permission inputs without activating runtime ownership

## What Remains Blocked

- all DiscordOS runtime/schema/data mutation
- all worker retargeting
- all Vercel cutover work
- all dual-read implementation
- all permission-policy ownership transfer
- preview/unfurl execution and gate reopening
- Playbook stashes
- Lifeline retained worktrees

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `DiscordOS feedback thread-sync adapter-consumer planning package 4`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- continue the tiny DiscordOS seam-planning chain one port at a time
- move next into the first side-effect seam only after the read-side and policy-facing surfaces are explicitly bounded
- route the Fitness generator-alignment mutation into the Fitness owner lane separately
- keep preview/unfurl closed until both its prerequisite and approval are satisfied

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-CONSUMER-PLANNING-PACKAGE-3-2026-05-26.md`

## Next Package

`DiscordOS feedback thread-sync adapter-consumer planning package 4`

Why:

- `FeedbackLookupPort` now covers identity resolution
- `FeedbackReportStorePort` now covers bounded read-side reference and lifecycle projection
- `FeedbackPermissionPort` now covers the broad staff-access decision seam
- `FeedbackThreadSyncPort` is the clearest next bounded planning surface without reopening runtime activation or ownership transfer
