# Durable Context Externalization

- Date: `2026-05-27`
- Mode: `docs-only marker definition, doctrine, and current-state assessment`
- Status: `initial marker admitted`

## Objective

Add `Durable Context Externalization` as a canonical ATLAS marker that measures how much critical operational continuity has been moved out of volatile GPT/Codex/chat-session carryover and into durable, deterministic, queryable artifacts across ATLAS and owner repos.

This lane is governance and control-plane work first.

It does not:

- move owner-repo source truth into ATLAS by default
- create speculative retrieval infrastructure
- claim automation or retrieval that is not already implemented
- widen ATLAS root into a runtime owner

## Canonical Surfaces Chosen

These were chosen as canonical because they are already the maintained restart and marker surfaces explicitly referenced by the book:

1. `docs/atlas-book/02-lanes-and-markers.md`
   - canonical marker table
2. `docs/atlas-book/12-restart-and-handoff-guide.md`
   - canonical continuation and resume surface
3. `docs/atlas-book/13-vision-and-endgames.md`
   - canonical endgame and marker-meaning surface
4. `docs/atlas-book/05-receipt-index.md`
   - canonical durable receipt spine
5. `docs/PLAYBOOK_NOTES.md`
   - canonical promoted doctrine note surface
6. `docs/memory/README.md`
   - canonical ATLAS memory doctrine surface

These surfaces were preferred over stale or derivative copies because:

- the restart guide explicitly says the durable book-local marker table lives in `02-lanes-and-markers.md`
- the restart guide is already the active continuation contract for new sessions
- the receipt index is already the maintained cross-reference spine
- the memory README already defines ATLAS durable memory posture

## Marker Definition

`Durable Context Externalization` measures the degree to which critical operational continuity is reconstructable from durable artifacts rather than dependent on model memory, chat history, or long-running session state.

It is specifically about whether operators and workers can resume work by retrieving:

- book chapters
- receipts
- continuation guides
- truth maps
- continuity notes
- prompt packs
- promoted doctrine
- repo-owned verification or adoption surfaces

instead of trusting conversational carryover as the primary continuity layer.

## Scoring Rubric

- `0%`
  - continuity is mostly trapped in chats, prompts, and operator memory
- `25%`
  - ad hoc receipts and checkpoints exist, but they are inconsistent, scattered, or non-canonical
- `50%`
  - canonical continuity artifacts exist and are used for major lanes, but retrieval-first use is not yet the default operating posture
- `75%`
  - retrieval-first continuity is documented and operational across major stack workflows
- `100%`
  - critical work is resumable and reconstructable from ATLAS plus owner-repo artifacts without depending on prior model or chat continuity

## Doctrine Meaning

This marker exists because long-lived GPT/Codex continuity is useful but non-authoritative.

The durable substrate should live in:

- ATLAS book surfaces
- ATLAS receipts
- ATLAS memory slots
- prompt packs and continuation guides
- owner-repo docs and verification/adoption surfaces

Owner repos remain truth owners.

ATLAS may hold:

- continuity
- projections
- receipts
- prompt packs
- truth maps
- governed summaries
- resumable operator state

ATLAS should not become a duplicate source-of-truth mirror for owner-repo runtime behavior or data.

## Operator-Facing Doctrine

### Rule: `External Context First`

Workers should retrieve durable context before trusting chat continuity.

Operational meaning:

- use the book first
- use receipts second
- use repo-owned verification/adoption surfaces third
- use chat continuity last

### Pattern: `Ephemeral Worker, Durable Substrate`

GPT/Codex are temporary reasoning workers.

Durable state lives in:

- ATLAS
- owner repos
- governed receipts
- promoted notes
- verification/adoption artifacts

### Failure Mode: `Recursive Context Rot Loop`

Repeated GPT -> Codex -> ATLAS -> Codex -> GPT cycles accumulate stale, duplicated, or degraded context unless they are bounded by durable checkpoints and retrieval-first flows.

Symptoms:

- conflicting summaries
- stale marker posture repeated as current
- work restarted from chat recap instead of latest receipt
- owner-repo truth duplicated into ATLAS prose
- new sessions inheriting outdated prompt assumptions

## Current Assessment

Initial marker assessment:

- `Durable Context Externalization: 60%`

This is conservative.

Why it is already above the ad hoc band:

- ATLAS already has a canonical marker table
- ATLAS already has a restart and handoff guide
- ATLAS already has a receipt spine
- ATLAS already has current-state and system-map chapters
- ATLAS already has canonical durable memory slots for operator context
- owner repos already hold workflow-specific truth docs and verification/adoption evidence

Why it is not yet in the retrieval-first high band:

- retrieval is still mostly manual, not enforced by shared tooling
- continuity manifests are partial rather than universal
- some major lane continuity still depends on operator judgment stitching together multiple receipts
- prompt/continuation doctrine existed, but not yet under one explicit `External Context First` marker and rubric
- the system still allows stale chat recaps to compete with current receipts unless the operator actively resists that drift

### Evidence Used

ATLAS evidence:

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/ATLAS_ASSISTANT_PROFILE.md`
- `docs/PLAYBOOK_NOTES.md`

Owner-repo evidence:

- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`
- repo-owned exports and verification surfaces already referenced from root receipts

## Before / After Doctrine Shift

Before:

- ATLAS already leaned toward durable receipts and restart docs, but the posture was distributed and only partially framed as a named continuity marker
- chat continuity was already de-prioritized in some surfaces, but not explicitly tracked as its own clean-and-re-sync program concern

After:

- the stack now has an explicit marker for externalizing continuity out of volatile session memory
- the continuation surface now states retrieval-first posture more explicitly
- the doctrine now names the worker/substrate split and the context-rot failure mode directly
- future marker reviews can score continuity durability independently from general documentation quality

## Ownership Boundary Note

No owner-repo truth boundary was violated in this pass.

This lane only changes:

- ATLAS marker surfaces
- ATLAS doctrine surfaces
- ATLAS continuation surfaces
- ATLAS durable receipt surfaces

It does not move owner-repo runtime or data truth into ATLAS.

## Exact Follow-On Work

These should be separate lanes:

1. `Durable Context Externalization continuity-manifest pass`
   - define a reusable continuity-manifest shape for major lanes
2. `Durable Context Externalization repo-owned retrieval surface inventory`
   - map which owner repos already expose verification/adoption continuity surfaces and which do not
3. `Durable Context Externalization prompt-pack normalization`
   - tighten active ATLAS prompt packs so retrieval-first behavior is universal rather than implied

## Rule

External Context First.

## Pattern

Ephemeral Worker, Durable Substrate.

## Failure Mode

Recursive Context Rot Loop.
