# AI Long-Run Batch Orchestration Queue-Or-Registry Post-Broader Attention_Queue Semantics Beyond Provenance Alerts Next-Slice Selection Pass 306 - 2026-06-15

- Date: `2026-06-15`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `docs-only root-bounded next-slice selection`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-CONTRACT-FREEZE-PASS-300-2026-06-15.md`
  - `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-QUEUE-OR-REGISTRY-BROADER-ATTENTION_QUEUE-SEMANTICS-BEYOND-PROVENANCE-ALERTS-PROMPT-PACK-AND-HANDOFF-CONTRACT-PASS-304-2026-06-15.md`
  - `docs/ops/ATLAS-STATUS-RUNBOOK.md`
  - `ops/cortex/render_status.py`
  - `tests/test_cortex_render_status_provenance.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
- Control-plane checkpoint: `main@8df5ab2b`

## Objective

Choose the strongest remaining bounded `attention_queue` follow-on now that the initiative-plus-provenance mixed-family slice is implementation-backed and proven on canonical `main`.

## Candidate Comparison

The strongest honest remaining next-slice candidates are:

1. the root-local `conversation_action_request` queue family
2. registry/session/worker/merge/trust-derived queue families
3. provenance-repair or broader orchestration-adoption work

## Selection

Select exactly one next slice:

- the root-local `conversation_action_request` queue family

## Why `conversation_action_request` Wins

- it is already in the pass-300 admitted item-family set, so the family is contract-visible without forcing a new queue taxonomy
- it stays root-local and descriptor-backed because it reads only `conversation_turn` descriptors already consumed inside `attention_queue(...)`
- it does not require registry-state, runtime-state, session-state, merge-state, trust-surface, or owner-repo mutation to explain its bounded payload behavior
- it remains narrower than the registry/session/worker/merge/trust families because those families lean on broader runtime or governance surfaces rather than one compact descriptor-backed operator-review seam
- it remains narrower than provenance repair or adoption work because it still concerns read-model queue semantics rather than mutation, cleanup, or operational rollout claims

## Deferred Alternatives

### Registry/session/worker/merge/trust-derived queue families

Deferred because:

- they depend on broader runtime and governance surfaces than the current smallest root-local follow-on
- they reopen more cross-surface contradiction and mutation-adjacent questions than the descriptor-backed conversation seam

Reopen condition:

- only after the `conversation_action_request` family is either frozen and bounded or honestly rejected

### Provenance repair or broader orchestration adoption

Deferred because:

- repair work widens into missing-file restoration, stale-ref cleanup, or other mutation families
- adoption work widens into supervisor/operator proof rather than one bounded queue-semantic seam

Reopen condition:

- only after the remaining root-local broader queue families are either frozen or exhausted

## Exact Next Package

- `AI Long-Run Batch Orchestration queue-or-registry broader attention_queue conversation_action_request contract freeze pass 307`

## Marker Decision

- `none`

Why:

- this pass chooses the next bounded slice only
- the implementation-backed movement already landed in the reconciliation receipt, so no second ratchet is justified here

## Rule

After the initiative-plus-provenance mixed-family queue slice lands, prefer the smallest remaining descriptor-backed queue family before reopening runtime-derived or mutation-adjacent queue work.
