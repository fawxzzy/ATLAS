# Cortex Workflow Profile Read-Model - 2026-05-25

## Summary

This lane adds the smallest explicit Cortex-side consumer for the canonical Zachariah Workflow Profile.

The goal is not to build Cortex memory ingestion. The goal is to make the canonical operator profile available inside the existing Cortex context packet and worker-prompt artifacts so future Cortex bootstrap flows consume the same source of truth that Codex bootstrap already reads.

## What changed

- added `ops/cortex/workflow_profile.py`
- added a deterministic workflow-profile payload to:
  - `ops/cortex/context_assembler.py`
  - `ops/cortex/worker_prompt.py`
- updated tests so Cortex artifacts now prove the canonical Zac profile is present
- repaired encoding drift in `docs/memory/profiles/zachariah_workflow_profile.md`
- updated `docs/ATLAS_ASSISTANT_PROFILE.md` so it truthfully describes the new minimal Cortex read-model

## Scope

Included:
- canonical profile metadata + markdown refs
- response-contract extraction
- preferred style extraction
- reasoning-route extraction
- canonical memory rule/pattern/failure-mode extraction
- Cortex context-packet and worker-prompt exposure

Not included:
- full Cortex memory ingestion
- memory promotion
- runtime adapter logic
- Playbook feature work
- cross-repo pattern learning

## Verification

Passed:
- `python -m unittest tests.test_cortex_context_assembler`
- `python -m unittest tests.test_cortex_worker_prompt`
- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`
- direct payload sanity for `ops.cortex.workflow_profile.build_workflow_profile_payload()`

Attempted but not re-ratified in this lane:
- `python -m unittest tests.test_atlas_codex_context`

The Codex-context suite timed out twice as ambient test debt. This lane does not modify `ops/atlas/build_codex_context.py`, and Codex bootstrap already had the canonical profile wired before this Cortex read-model change.

## Rule

Canonical user/project context belongs in versioned Atlas memory slots, not only in external assistant memory.

## Pattern

Use a small `AGENTS.md` pointer plus a full durable memory slot. Keep `AGENTS.md` lightweight, keep the full profile in the canonical slot, and expose a narrow read-model to Cortex or Codex consumers instead of duplicating profile truth.

## Failure Mode

If Cortex bootstrap relies on implicit chat memory or ad hoc copied summaries instead of the canonical profile slot, operator behavior drifts across tools and new sessions lose response-shape consistency.
