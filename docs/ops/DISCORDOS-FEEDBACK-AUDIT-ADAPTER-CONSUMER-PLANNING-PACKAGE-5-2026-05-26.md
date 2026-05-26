# DiscordOS Feedback Audit Adapter-Consumer Planning Package 5 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback audit adapter-consumer planning package 5`
- Mode: `docs-only seam planning`
- Control-plane checkpoint: `main@a3c63c5`

## Scope

Plan exactly one named DiscordOS feedback adapter-consumer seam after:

- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-CONSUMER-PLANNING-PACKAGE-3-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-CONSUMER-PLANNING-PACKAGE-4-2026-05-26.md`

Chosen port:

- `FeedbackAuditPort`

In scope:

- one named feedback port surface
- its producer/source surface
- its future consumer surface
- its contract shape and ownership boundary

Out of scope:

- DiscordOS runtime activation
- DiscordOS schema/data mutation
- audit-truth ownership transfer
- generic Discord write ownership transfer
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
- the seam stays append-bounded and non-activating
- no owner-repo tracked content is changed
- Fitness remains the canonical audit-posting owner for live feedback flows
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@a3c63c5f8a9c67a978b478584db578ca73d840f1`
- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-CONSUMER-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-CONSUMER-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-CONSUMER-PLANNING-PACKAGE-3-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-CONSUMER-PLANNING-PACKAGE-4-2026-05-26.md`
- `docs/ops/PREVIEW-UNFURL-AND-DISCORDOS-FOLLOW-ON-QUEUE-REASSESSMENT-2026-05-26.md`
- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-DOMAIN-EXTRACTION-READINESS-2026-05-25.md`
- `docs/ops/DISCORD-FEEDBACK-RUNTIME-BOUNDARY-PACKAGE-1-2026-05-25.md`
- `repos/DiscordOS/docs/contracts/feedback-runtime.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`

## Chosen Port

Selected fifth port:

- `FeedbackAuditPort`

Current contract shape:

```ts
interface FeedbackAuditPort {
  postAuditEvent(event: FeedbackAuditEvent): Promise<DiscordOSFeedbackResult<{ messageId: string | null }>>;
}
```

## Why This Port Was Chosen

`FeedbackAuditPort` is the right fifth seam because:

- packages 1 through 4 already bounded identity, read-side store projections, broad staff-access policy, and thread-sync side effects
- audit remains the last major named side-effect seam already present in the contract surface
- the current Fitness boundary already isolates audit posting behind an event-shaped helper instead of scattering it across raw route code

Why it stays small enough:

- it covers append-only audit comment posting, not general Discord thread mutation
- it does not absorb starter-message sync, forum title/tag sync, or resolved-reaction behavior
- it does not approve runtime activation, schema landing, or worker retarget
- it keeps the side-effect seam categorized by event append behavior instead of widening into a generic “write to Discord” surface

Why it is not a generic Discord write seam:

- the event contract is already typed and category-limited
- the current helper posts to an existing feedback thread using report-local context rather than arbitrary channel writes
- broadening this port here would collapse audit semantics into a catch-all side-effect bus

## Producer / Source Surface

Current Fitness-owned producer side:

- `postFeedbackAuditComment(...)` in `repos/fawxzzy-fitness/src/lib/discord/runtime/feedback/forum.ts`
- route-level audit wrapper in `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- event-triggering call sites in the Fitness route for:
  - `duplicate_signal`
  - `status_update`
  - `completion_review`
  - `reporter_update`
  - `staff_update`
  - `withdraw`

Current append/write boundary:

- audit writes are append-only replies into the existing feedback forum thread
- the helper returns a bounded `{ ok, messageId }` result
- audit posting does not claim ownership of starter-message sync or forum-state persistence

What stays Fitness-owned:

- live Discord REST execution for audit comment posting
- event sequencing inside the Fitness-hosted route
- the decision about when an audit event should be emitted
- the composition between report row truth, lifecycle state, and event payload details
- current soft-failure logging behavior for audit posting failures

## Consumer Surface

First future consumer class for this seam:

- DiscordOS feedback consumers that already have lookup/store/permission/thread-sync context and need to request a bounded audit append without importing Fitness audit helper logic directly

Consumer examples the seam should eventually support:

- lifecycle updates that need a status-change audit reply
- completion-review flows that need a review-decision audit reply
- reporter/staff content edits that need a change-summary audit reply
- withdraw or duplicate flows that need a small immutable trail in the existing thread

Current rule:

- this packet plans the audit boundary only
- it does not implement a DiscordOS audit adapter, route handler, or generic Discord writer

## Contract Boundary

### Input

- `event: FeedbackAuditEvent`

Current event categories already represented by the contract:

- `status_update`
- `completion_review`
- `withdraw`
- `reporter_update`
- `staff_update`
- `duplicate_signal`
- `sync_format`

Current minimum event fields:

- `reportId`
- `action`
- `actorLabel`
- `includeReporterMention`
- `statusBefore`
- `statusAfter`
- `completionReviewStatus`
- `note`
- `duplicateCount`

### Output

- `DiscordOSFeedbackResult<{ messageId: string | null }>`

Normalized success shape:

- the result may include a Discord message id when an audit comment is posted
- the result may include `messageId: null` when no thread exists and the current owner treats the audit step as a no-op success

### Failure Contract

This method should use the existing `DiscordOSFeedbackResult<T>` envelope and normalize failures into the current shared error family where relevant:

- `AUDIT_COMMENT_FAILED`
- `REPORT_NOT_FOUND`
- `UPSTREAM_UNAVAILABLE`
- `INVALID_INPUT`

Important normalization rule:

- raw Discord REST details and owner-specific audit helper internals must not become DiscordOS-owned contract truth
- the future adapter should translate current Fitness audit-posting failures into the shared result shape before a DiscordOS consumer sees them

## Composition With Earlier Seams

Planned future composition:

1. `FeedbackLookupPort`
   - resolves the target report identity
2. `FeedbackReportStorePort`
   - provides report reference and lifecycle context
3. `FeedbackPermissionPort`
   - answers broad staff-access questions where relevant
4. `FeedbackThreadSyncPort`
   - handles bounded thread-sync side effects
5. `FeedbackAuditPort`
   - appends the bounded audit event for the already-determined lifecycle action

Why composition matters:

- audit should be downstream of the identity, state, and policy seams
- audit should not become the place where route logic, state derivation, or thread-sync behavior gets reinvented
- thread-sync and audit remain separate categories even when the same user action triggers both

## Ownership Boundary

### Fitness keeps

- canonical report-row truth
- live route orchestration for when audit is emitted
- live Discord REST execution for thread replies
- event payload derivation from current row state and current action context
- current soft-failure and partial-success handling

### DiscordOS later receives

- a bounded audit-append request surface
- a normalized event-based result shape
- no ownership of the underlying report row
- no ownership of thread-sync behavior through this port
- no ownership of the current Discord runtime host

Boundary rule:

- `FeedbackAuditPort` is an audit-append seam, not runtime ownership

## Data Flow

Planned future flow:

1. a DiscordOS feedback consumer already knows the target `reportId`
2. the consumer composes lookup/store/permission/thread-sync seams as needed
3. the consumer builds a bounded `FeedbackAuditEvent`
4. the consumer calls `postAuditEvent(event)`
5. the Fitness-owned adapter resolves the current thread target and appends the audit comment if appropriate
6. the adapter returns either:
   - normalized `{ messageId }` success
   - normalized `DiscordOSFeedbackResult` failure

## Explicit Non-Goals

This package does not plan or approve:

- generic Discord message posting outside feedback audit
- starter-message sync through the audit port
- forum title or tag synchronization through the audit port
- route-level lifecycle decision ownership through the audit port
- schema landing
- dual-read proof
- worker retarget
- runtime activation

Rule:

- Audit seam is not runtime ownership

Pattern:

- Side-effect seams stay separated by category

Failure Mode:

- Generic Discord write ownership by planning language

Why thread-sync stays out of this seam:

- package 4 already bounded starter-message, forum-state, and resolved-reaction sync
- collapsing those into audit would erase the separation that now exists in both the Fitness boundary and the contract surface

## Allowed Future Follow-On Packages

Allowed next tiny planning packets after this one:

1. `DiscordOS feedback seam-chain implementation-readiness checkpoint`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Why the readiness checkpoint is next:

- the named feedback contract seam chain is now fully packetized across lookup, store, permission, thread-sync, and audit
- the next safe ATLAS-root move is to reassess whether the seam chain is complete enough for any repo-local adapter implementation planning, rather than sliding straight into mutation by momentum

## What Remains Blocked

- all DiscordOS runtime/schema/data mutation
- all worker retargeting
- all Vercel cutover work
- all dual-read implementation
- all generic Discord write ownership transfer
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

1. `DiscordOS feedback seam-chain implementation-readiness checkpoint`
2. `Fitness Brand Generator Alignment Package`
3. `Preview Cache Remote And Unfurl Verification` only after explicit deploy-backed lane opening

Recommended ordering:

- stop the one-port planning chain here and reassess implementation readiness explicitly
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
- `docs/ops/DISCORDOS-FEEDBACK-AUDIT-ADAPTER-CONSUMER-PLANNING-PACKAGE-5-2026-05-26.md`

## Next Package

`DiscordOS feedback seam-chain implementation-readiness checkpoint`

Why:

- `FeedbackLookupPort` now covers identity resolution
- `FeedbackReportStorePort` now covers bounded read-side reference and lifecycle projection
- `FeedbackPermissionPort` now covers the broad staff-access decision seam
- `FeedbackThreadSyncPort` now bounds the thread-sync side-effect surface
- `FeedbackAuditPort` now bounds the append-only audit side-effect surface
- the next safe question is whether this full seam chain is ready for any repo-local implementation planning without reopening runtime ownership transfer
