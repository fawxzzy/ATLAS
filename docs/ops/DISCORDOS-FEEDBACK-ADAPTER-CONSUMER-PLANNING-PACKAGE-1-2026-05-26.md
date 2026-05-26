# DiscordOS Feedback Adapter-Consumer Planning Package 1 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback adapter-consumer planning package 1`
- Mode: `docs-only seam planning`
- Control-plane checkpoint: `main@a4d8108`

## Scope

Plan exactly one named DiscordOS feedback adapter-consumer seam after the queue reassessment recorded in:

- `docs/ops/PREVIEW-UNFURL-AND-DISCORDOS-FOLLOW-ON-QUEUE-REASSESSMENT-2026-05-26.md`

Chosen port:

- `FeedbackLookupPort`

In scope:

- one named feedback port surface
- its producer/source surface
- its future consumer surface
- its contract shape and ownership boundary

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- worker retarget
- Vercel cutover
- dual-read implementation
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`

## Operating Posture

- ATLAS root remains the coordination and receipt layer
- this pass is planning only
- the packet stays tied to one named feedback port
- no owner-repo tracked content is changed
- preview/unfurl approval stays closed
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@a4d810840a74d948809784fc1efd6bb5f5536b21`
- `docs/ops/PREVIEW-UNFURL-AND-DISCORDOS-FOLLOW-ON-QUEUE-REASSESSMENT-2026-05-26.md`
- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`
- `docs/ops/DISCORD-OS-POST-BOOTSTRAP-CODE-INVENTORY-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`

## Chosen Port

Selected first port:

- `FeedbackLookupPort`

Current contract shape:

```ts
interface FeedbackLookupPort {
  findReportIdentity(reportIdOrPrefix: string): Promise<DiscordOSFeedbackResult<FeedbackCardIdentity>>;
}
```

## Why This Port Was Chosen

`FeedbackLookupPort` is the smallest justified first seam because:

- the readiness gate explicitly calls out `feedback report lookup by report id or prefix`
- the same gate explicitly calls out `lookup-result and failure-code normalization across the seam`
- the current Fitness feedback boundary already isolates lookup-failure messaging in `src/lib/discord/runtime/feedback/helpers.ts`
- the lookup seam is read-only and does not require schema landing, thread mutation, audit posting, or runtime activation
- it creates a stable first consumer boundary without forcing DiscordOS to inherit the full Fitness report row shape

Why it wins over the other ports right now:

- `FeedbackReportStorePort` still carries more current-row detail and is better planned second
- `FeedbackThreadSyncPort` and `FeedbackAuditPort` are side-effecting seams and should not be the first consumer boundary
- `FeedbackPermissionPort` is narrow, but it is less central than report identity resolution for the first end-to-end planning seam

## Producer / Source Surface

Current Fitness-owned producer side:

- feedback report lookup in `repos/fawxzzy-fitness/src/lib/discord/bug-reports.ts`
- lookup-failure normalization helpers in `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/helpers.ts`
- canonical source rows in Fitness table `discord_feedback_reports`

What stays Fitness-owned:

- the canonical feedback report row
- lookup by full report id or prefix
- ambiguity resolution against the Fitness-hosted report corpus
- any direct Supabase access needed to resolve the lookup

## Consumer Surface

First future consumer class for this seam:

- DiscordOS feedback manage/report-targeting flows that need to resolve a report identity before later lifecycle actions

Consumer examples the seam should eventually support without copying the full Fitness route:

- manage lookup modal flows
- future status-update targeting
- future completion-review targeting
- future withdraw targeting

Current rule:

- this packet plans the consumer boundary only
- it does not implement a DiscordOS consumer, modal, route, or runtime handler

## Contract Boundary

### Input

- `reportIdOrPrefix: string`

### Output on success

- `FeedbackCardIdentity`

Minimum fields already defined by the contract:

- immutable `reportId`
- `reportType`
- optional `shortDisplayId`
- `createdAt`
- `updatedAt`

### Output on failure

Use the existing `DiscordOSFeedbackResult<T>` envelope and normalize Fitness lookup outcomes into the contract error family:

- `REPORT_NOT_FOUND`
- `REPORT_ID_AMBIGUOUS`
- `UPSTREAM_UNAVAILABLE`
- `INVALID_INPUT` when the user-provided value is structurally unusable

Important normalization rule:

- raw Fitness-specific lookup failure details must not leak through as DiscordOS-owned contract truth
- the adapter should convert current Fitness lookup outcomes into the contract result shape before any future DiscordOS consumer uses them

## Ownership Boundary

### Fitness keeps

- report-row truth
- report-id/prefix lookup execution
- Supabase access and row selection logic
- current live lookup behavior inside the Fitness-hosted runtime

### DiscordOS later receives

- a read-only identity-resolution seam
- a transport-safe result envelope
- no direct ownership of the underlying report row in this package

Boundary rule:

- `FeedbackLookupPort` is an identity-resolution seam, not a row-ownership transfer seam

## Data Flow

Planned future flow:

1. a DiscordOS feedback consumer receives a user-supplied report id or prefix
2. the consumer calls `FeedbackLookupPort.findReportIdentity(reportIdOrPrefix)`
3. the Fitness-owned adapter resolves the report against `discord_feedback_reports`
4. the adapter returns either:
   - normalized `FeedbackCardIdentity`, or
   - normalized `DiscordOSFeedbackResult` failure
5. the consumer decides whether to continue a later lifecycle flow or return a lookup-failure response

## Explicit Non-Goals

This package does not plan or approve:

- direct DiscordOS access to `discord_feedback_reports`
- lifecycle-state reads
- feedback row persistence
- forum title/tag synchronization
- audit comment posting
- permission evaluation migration
- schema landing
- row export or migration
- worker retarget
- runtime activation

## Allowed Future Follow-On Packages

Allowed next tiny planning packets after this one:

1. `DiscordOS feedback report-store adapter-consumer planning package 2`
2. `DiscordOS feedback permission adapter-consumer planning package 3`
3. `DiscordOS feedback thread-sync adapter-consumer planning package` only after the read-side seam order remains clear

Why `FeedbackReportStorePort` is the clearest next packet:

- the readiness gate lists `FeedbackReportStorePort` in the minimum first contract set
- it can stay read-side and upstream-owned while defining the next larger data boundary after identity lookup
- it still avoids runtime activation and side-effecting Discord writes

## What Remains Blocked

- all DiscordOS runtime/schema/data mutation
- all worker retargeting
- all Vercel cutover work
- all dual-read implementation
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

1. `DiscordOS feedback report-store adapter-consumer planning package 2`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- continue the tiny DiscordOS read-side planning chain one seam at a time
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
- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`

## Next Package

`DiscordOS feedback report-store adapter-consumer planning package 2`

Why:

- `FeedbackLookupPort` is now planned as the first read-side seam
- `FeedbackReportStorePort` is the clearest next tiny planning surface from the readiness gate
- broader runtime/schema/activation work remains blocked
