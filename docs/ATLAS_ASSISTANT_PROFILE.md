# ATLAS Assistant Profile

## Purpose

ATLAS stores durable operator and assistant context in versioned project files, not only in external saved-memory systems.

The current canonical profile is:

- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/memory/profiles/zachariah_workflow_profile.json`

## Canonical source of truth

The Zachariah Workflow Profile is the canonical durable memory slot for:
- assistant behavior preferences
- long-term project context
- Playbook facts
- Cortex roadmap guidance
- Atlas integration and bootstrap context

ChatGPT saved memory is a convenience cache only. Atlas is the durable source of truth.

## Intended consumers

This profile should be read by:
- future Atlas workflows
- future Cortex bootstrap and context assembly flows
- Codex sessions working in Atlas
- Playbook planning flows
- assistant-profile ingestion systems

Agents working in Atlas should read this profile before planning Playbook, Cortex, Atlas, Codex-prompt, or repo-architecture work.

The current Cortex integration is intentionally small:
- Cortex context assembly consumes the canonical workflow profile as an explicit read-model
- Cortex worker prompts mirror the same response-contract and style guidance
- this does not implement full Cortex ingestion, memory promotion, or runtime decisioning

## Memory architecture guidance

Rule:
Canonical user/project context belongs in versioned Atlas memory slots, not only in external assistant memory.

Pattern:
Use a small `AGENTS.md` pointer plus a full durable memory slot. Keep `AGENTS.md` lightweight and keep the full profile in the canonical slot.

Failure Mode:
If profile context only lives in ChatGPT saved memory, it can be lost, compressed, omitted, or become unavailable across tools. Avoid relying on it as the sole source of truth.

## Scope note

This change provides durable context storage, discovery, and a minimal Cortex read-model.

It does not:
- implement full Cortex ingestion or runtime memory orchestration
- implement Playbook features
- implement cross-repo pattern learning
- introduce a second hidden memory system
