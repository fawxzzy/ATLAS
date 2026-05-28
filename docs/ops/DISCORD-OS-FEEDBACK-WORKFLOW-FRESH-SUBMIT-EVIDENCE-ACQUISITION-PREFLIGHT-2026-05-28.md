# Discord OS Feedback Workflow Fresh-Submit Evidence Acquisition Preflight - 2026-05-28

- Date: `2026-05-28`
- Lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `docs-only proof-acquisition preflight`
- Marker posture: `Discord OS Feedback Workflow Canonicalization: 72%`
- Source surfaces:
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-FRESH-SUBMIT-POSITIVE-LIVE-PROOF-CAPTURE-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-MARKER-RATCHET-CHECKPOINT-6-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-LIVE-PROOF-CRITERIA-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-NO-REGRESSION-LIVE-PARITY-GAP-PACKET-2026-05-27.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-FEEDBACK-BOARD.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-VERIFICATION.md`

## Objective

Freeze the exact prerequisites, evidence fields, and operator capture method needed to land one positive fresh-submit live proof receipt later for one bounded class only:

- fresh report id
- bounded row evidence
- thread id
- starter message id
- linkage proof from the same event

This pass does not:

- approve runtime migration
- approve schema migration
- approve owner transfer
- claim DiscordOS owns the live runtime
- widen the proof standard beyond the already-frozen fresh-submit class

## Root State

- branch: `main`
- HEAD: `4bcbe67`
- status: clean except intentional untracked `archive/`
- validation: green before preflight drafting at `critical=0 error=0 warning=310`

## Why This Pass Exists

The lane already knows the exact missing class:

- one positive fresh-submit live proof showing:
  - bounded row first
  - thread second
  - stable report/thread/message linkage

What is still missing is the acquisition plan precise enough to let a later owner-side live capture land that proof in one pass instead of another vague recheck.

## Exact Positive-Proof Target

A future positive receipt counts only if one single fresh submit event can prove all of the following together:

1. a fresh report row was created through the live member-facing submit path
2. the row existed first or was committed first
3. the linked feedback thread was created second
4. the starter message belongs to that same thread
5. report id, thread id, and starter message id all tie back to the same event

## Preflight Prerequisites

The later live capture must not start unless all of the following are true first:

1. the Fitness-owned launcher is live in `feedback-submission`
2. the live submit path is using the current launcher/button flow rather than a legacy setup surface
3. the operator has read-only access to capture the resulting forum thread and starter message details
4. the operator can obtain one bounded row truth artifact after the submit event without mutating the row again
5. the event is a truly fresh submit, not an edit, repair, sync, duplicate fold, or historical shipped-card lookup

If any of those are not true, the later capture should fail closed as `not yet provable`.

## Exact Evidence Bundle Required Later

The later positive-proof receipt must include exactly one evidence bundle with the following fields.

### Core identity fields

- full fresh report id
- optional short id if visibly available
- report type
- status captured immediately after submit

### Bounded row fields

- report id from owner truth
- row-presence proof for that id
- `created_at` or equivalent row-timestamp evidence
- linked forum thread id stored on the row
- linked forum starter message id stored on the row, if the row stores it directly

### Discord thread fields

- thread id
- starter message id
- thread URL or starter-message permalink
- visible starter post showing the same fresh report id

### Same-event linkage fields

- one timestamp window or equivalent event-window attestation tying the row and thread capture to the same submit event
- one mapping statement confirming:
  - row report id = visible report id
  - row thread id = captured thread id
  - row starter message id or resolved starter post = captured starter message id

### Optional but allowed support fields

- launcher channel id
- launcher message id
- ephemeral success copy or screenshot
- operator capture timestamp

These support fields may strengthen the receipt.

They are not substitutes for the core row/thread/message bundle.

## Exact Proof Requirements Per Field

| Required proof element | Minimum acceptable evidence | What does not count |
| --- | --- | --- |
| Fresh report id | full UUID copied from the created forum card or owner truth artifact from the same event | historical report id from an older shipped card |
| Bounded row evidence | one owner-truth row artifact proving the new report id exists after submit | launcher existence or code intent alone |
| Thread id | one captured thread id from the created feedback thread | a later unrelated thread id from a repair or sync path |
| Starter message id | one captured starter-message id or starter-message permalink from the created thread | an audit-comment id or a later mutation message |
| Same-event linkage | one receipt section tying row, thread, and starter message to the same submit window | separate receipts from unrelated times |
| Row first, thread second | one owner-side sequence attestation or artifact ordering that supports row before thread | doctrine saying the sequence is supposed to work that way |

## Audit-Trace Rule For This Proof Class

Audit trace is not a required same-event proof field for fresh submit.

Why:

- owner doctrine requires audit comments for post-creation mutations
- fresh submit is the creation event itself
- requiring a same-event audit comment here would widen the proof standard beyond the lane's current contract

Allowed:

- include a compact same-event follow-up trace if the live surface happens to emit one

Not required:

- a thread-visible audit comment from the creation event itself

## Minimal Operator Capture Sequence

The later live owner-side capture should use this exact minimal sequence:

1. Confirm the canonical launcher is live in `feedback-submission`.
2. Submit one new non-testing feedback card through the member-facing `Submit` launcher path.
3. Preserve the capture window immediately:
   - operator date/time
   - launcher channel
   - confirmation that this was a fresh submit, not edit or withdraw
4. Open the created feedback thread.
5. Copy and preserve from the created thread:
   - full report id shown on the starter post
   - thread id
   - starter message id or direct starter-message permalink
   - thread URL
6. Preserve one bounded row truth artifact for that same report id from the Fitness-owned truth surface.
7. Confirm the row artifact and Discord thread artifact agree on:
   - report id
   - thread id
   - starter message id, if stored directly, or equivalent starter-post linkage
8. Freeze one same-event sequencing statement explaining why the artifact set supports:
   - bounded row first
   - thread second
9. Stop.

The later proof capture should not widen into edit-flow, completion-review, updates, or extraction parity work.

## Preferred Capture Method

Preferred later capture method:

- live launcher submit through the Fitness-owned production path
- immediate thread capture from the created forum thread
- one owner-side read-only bounded row artifact captured by report id
- one root receipt that packages only those artifacts and the sequencing conclusion

This preflight does not require a specific new helper command to exist first.

It only requires that the later proof bundle contain the exact fields above from the owner truth surfaces.

## What The Later Receipt Must Say Explicitly

The later positive-proof receipt must state explicitly:

- who submitted the fresh card class
- that the event came from the live Fitness-owned submit path
- how the full report id was obtained
- how the thread id and starter message id were obtained
- how bounded row evidence was obtained
- why the evidence supports row first and thread second
- what exact regression would invalidate the proof later

## Fail-Closed Conditions

The later attempt must fail closed if any of the following happen:

- the created thread lacks a visible fresh report id
- the operator cannot recover the starter message id
- the bounded row artifact cannot be tied back to the same report id
- thread id and row linkage disagree
- the evidence bundle proves linkage but not same-event sequencing
- the event turns out to be an edit, repair, or historical card rather than a fresh submit

## What This Preflight Does Not Approve

This preflight does not approve:

- runtime migration
- schema migration
- owner transfer
- DiscordOS live runtime ownership
- broad fresh-submit parity
- no-regression extraction parity

Current live owner remains:

- Fitness

Current DiscordOS posture remains:

- future ownership target only

## Result

The missing fresh-submit proof class is now acquisition-ready at the governance layer.

What remains missing is not the evidence standard.

It is one later owner-side live capture that actually produces the frozen bundle:

- fresh report id
- bounded row proof
- thread id
- starter message id
- same-event linkage
- row-first / thread-second sequencing support

## Exact Next Package

`Discord OS Feedback Workflow fresh-submit positive live proof receipt only after one owner-side evidence bundle is captured`

Why:

- the preflight now freezes the exact fields and sequence
- another proof-gap restatement would add no value
- the next meaningful change is the actual evidence bundle

## Rule

Preflight must define exactly how to capture the missing proof, not broaden the proof standard.

## Failure Mode

A preflight pass stays vague, so the positive proof gap remains blocked for another cycle.
