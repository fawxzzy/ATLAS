# Cortex Dual-Mode Replacement Readiness primary-operator acceptance and receipt contract freeze

- Date: `2026-07-14`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root primary-operator contract freeze`
- Scope: `freeze deterministic internal Cortex plan acceptance, operator dispatch correlation, and durable receipt behavior while retaining _stack execution ownership and optional external adapters`
- Marker movement: none; remains `90%`

## Decision

The stale selector packet for the synthesis-to-execution bridge schema is superseded. That schema, its planner, replay harness, and two real Atlas bridge lanes already exist.

The actual remaining ladder is:

1. Cortex internal primary-operator acceptance and receipt path
2. Cortex replay-backed primary-operator parity
3. Cortex optional-adapter endgame ratchet

This packet freezes step 1 without claiming implementation or `100%` readiness.

## Contract

Machine-readable doctrine:

- `docs/registry/CORTEX-PRIMARY-OPERATOR-ACCEPTANCE-RECEIPT-CONTRACT.v1.json`

Schemas:

- `atlas.cortex.primary_operator_acceptance.v1`
- `atlas.cortex.primary_operator_receipt.v1`

The primary operator consumes one `atlas.cortex.execution_plan.v1` plus explicit authority, resource-lease, and truth-digest inputs. It deterministically accepts, blocks, or rejects the plan before any dispatch.

## Ownership

- Cortex accepts/rejects governed plans and correlates receipts.
- `_stack` remains the local execution/operator plane.
- Atlas owns global identity, contracts, final reconciliation, and markers.
- DiscordOS remains the sole logical board and Discord writer.
- ChatGPT and Codex adapters are optional transport surfaces, not truth authority.

## First implementation boundary

Allowed:

- `ops/cortex/primary_operator.py`
- `tests/test_cortex_primary_operator.py`
- explicit output under `tmp/atlas/**.json`

The first implementation is dry-run acceptance and receipt generation only. Runtime dispatch remains false until acceptance behavior is proven.

Required proof includes deterministic IDs, safe-plan acceptance, unsafe-plan rejection, authority-widening rejection, stale-truth rejection, lease-conflict rejection, optional-adapter posture, safe paths, and zero execution side effects.

## Marker decision

The marker remains `90%`.

The contract alone does not prove an internal primary operator. `100%` still requires real dispatch through `_stack`, durable correlated results, and replay-backed parity with ChatGPT/Codex treated as optional adapters.

## Exact next packet

```text
Cortex Dual-Mode Replacement Readiness primary-operator acceptance and receipt first implementation
```

## Reusable knowledge

**RULE - Acceptance precedes execution**

An internal reasoning system must durably accept a bounded authority envelope before it can ask the operator plane to execute.

**PATTERN - Internal operator, external adapters**

Cortex owns deterministic acceptance and correlation; `_stack` executes; ChatGPT/Codex may transport work but are not required sources of truth.

**FAILURE MODE - Advisory-to-operator overclaim**

A planner is called a primary operator before it can durably accept, dispatch, and reconcile one real job.
