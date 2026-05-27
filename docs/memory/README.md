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
