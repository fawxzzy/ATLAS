# ATLAS Memory

ATLAS uses more than one durable memory surface.

## Canonical rule

Rule:
Canonical user/project context belongs in versioned Atlas memory slots, not only in external assistant memory.

Pattern:
Use a small `AGENTS.md` pointer plus a full durable memory slot. Keep `AGENTS.md` lightweight and keep the full profile in the canonical slot.

Failure Mode:
If profile context only lives in ChatGPT saved memory, it can be lost, compressed, omitted, or become unavailable across tools. Avoid relying on it as the sole source of truth.

## Memory surfaces

- `docs/memory/profiles/**`
  - manual durable profile slots for operator and assistant bootstrap context
- `docs/memory/plans/**`
- `docs/memory/decisions/**`
- `docs/memory/initiatives/**`
- `docs/memory/hypotheses/**`
  - governed structured working-memory artifacts authored from explicit session and runtime sources

## Canonical operator profile

- Markdown: `docs/memory/profiles/zachariah_workflow_profile.md`
- Metadata: `docs/memory/profiles/zachariah_workflow_profile.json`

This is the current canonical durable source for Zachariah's assistant behavior preferences, long-term project context, Playbook facts, Cortex roadmap, Atlas memory strategy, and future bootstrap guidance.

ChatGPT saved memory is a convenience cache only. Atlas is the durable source of truth.

## Retrieval-first continuity doctrine

Rule:
External Context First.

Pattern:
Ephemeral Worker, Durable Substrate.

Failure Mode:
Recursive Context Rot Loop.

Meaning:

- workers should retrieve durable ATLAS and owner-repo context before trusting conversational continuity
- GPT/Codex are temporary reasoning workers, not the durable state substrate
- repeated chat-to-chat or worker-to-worker handoff without checkpointing will accumulate stale or duplicated context unless it is bounded by receipts, promoted notes, truth maps, and continuation guides

Preferred retrieval order:

1. continuity manifest when one exists
2. current book chapter
3. governing receipt chain
4. owner-repo truth-owner surface
5. verification/adoption surface
6. transcript nuance only when still unpromoted

Continuity-manifest rule:

- when a lane has a maintained continuity manifest, retrieve it before reconstructing state from chat recap or memory of the last session
- a continuity manifest is a retrieval map, not a second truth store
- a lane may claim `manifest-backed` continuity only when an active ATLAS-root manifest points to the current decisive receipt, owner truth-owner surfaces, and relevant verification/adoption surfaces
- a lane may claim `manifest-backed` continuity only while that manifest is still fresh enough to match the current checkpoint, marker posture, blocked work, and next-package posture
- otherwise treat the lane as receipt-backed or operator-stitched, not fully manifest-backed

First adoption posture:

- seed manifests first for cross-repo or cross-surface lanes with dense receipt chains
- prefer `Durable Context Externalization`, `Local Data Gateway`, `Discord OS Feedback Workflow Canonicalization`, and `Discord OS Infrastructure Separation` as first-adoption lanes
- do not apply the label `manifest-backed` before restart can actually follow the manifest chain without transcript-first reconstruction

## Retrieval surface taxonomy

Use this taxonomy when deciding what kind of durable context a surface provides:

- Canonical retrieval surface
  - restart, marker, map, receipt-index, or memory-slot surfaces meant to be read first
- Governed summary / promotion surface
  - promoted doctrine notes and lane receipts that compress durable truth for reuse
- Owner-repo truth-owner surface
  - repo-owned docs, contracts, adoption notes, and verification surfaces that define repo-local truth directly
- Non-authoritative memory / transcript residue
  - chat recap, prompt carryover, and scratch narrative that may help with nuance but must never override the durable surfaces above

## Continuity manifests

Continuity manifests are ATLAS-root retrieval maps for major lanes.

Canonical active manifest location:

- `docs/memory/initiatives/continuity-manifest-*.json`

They should:

- identify the active lane
- point to the current governing receipt chain
- point to owner-repo truth-owner surfaces
- point to verification/adoption surfaces
- record current blocked or gated work
- record the next package ladder

They should not:

- duplicate owner-repo source truth
- copy full receipt bodies
- become a parallel mutable truth store

Current first-adoption seeded manifests:

- `docs/memory/initiatives/continuity-manifest-durable-context-externalization.json`
- `docs/memory/initiatives/continuity-manifest-local-data-gateway.json`
- `docs/memory/initiatives/continuity-manifest-discord-os-feedback-workflow-canonicalization.json`
- `docs/memory/initiatives/continuity-manifest-discord-os-infrastructure-separation.json`

These seeded manifests make those lanes manifest-backed for restart routing.

They do not imply:

- universal manifest coverage across all lanes
- automated restart
- freedom to skip the cited owner truth-owner and verification/adoption surfaces
- permanent freshness without later refresh work

Refresh discipline:

- a manifest becomes stale when a newer decisive receipt, newer marker posture, newer blocked-work posture, or newer next-package ladder exists than the manifest records
- a stale manifest should be treated as `manifest-present only`
- restart should then fall through to the current decisive receipt chain and current marker surfaces until the manifest is refreshed
