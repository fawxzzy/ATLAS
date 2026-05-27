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

Continuity-manifest rule:

- when a lane has a maintained continuity manifest, retrieve it before reconstructing state from chat recap or memory of the last session

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
