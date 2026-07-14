# Cortex Dual-Mode Replacement Readiness primary-operator first implementation reconciliation

- Date: `2026-07-14`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `root-owned deterministic dry-run primary operator`
- Marker movement: none; remains `90%`

## Executed state

The first internal primary-operator boundary is implemented in:

- `ops/cortex/primary_operator.py`
- `tests/test_cortex_primary_operator.py`

It consumes one `atlas.cortex.execution_plan.v1` plus explicit authority, current lease, and root-truth inputs. It emits correlated `atlas.cortex.primary_operator_acceptance.v1` and `atlas.cortex.primary_operator_receipt.v1` objects.

## Proven behavior

- identical admitted inputs produce stable acceptance and receipt identities;
- ready and explicitly safe plans are accepted;
- unsafe plans and widened authority are rejected;
- stale truth and resource-lease conflicts block admission;
- ChatGPT and Codex adapters are optional transport surfaces;
- outputs are restricted to explicit `tmp/atlas/**.json` paths;
- runtime dispatch and mutation remain false;
- `_stack` remains the named operator plane.

Focused proof: `13` tests passed.

Combined Cortex regression proof: `122` tests passed across the primary operator, execution planner, replay harness, synthesis packet generator, and Codex closeout-ingestion read model.

## Authority result

This implementation does not launch Codex, invoke `_stack`, write Discord, move cards, mutate owner repositories, push Git, deploy, query a live platform, read secrets, or move markers.

Full host capability remains separate from task and external-action authority.

## Marker decision

The lane remains `90%`.

Dry-run acceptance and receipt correlation are now implemented, but `100%` still requires:

1. an admitted runtime dispatch through `_stack`;
2. a durable result correlated back to the acceptance identity;
3. replay-backed parity proving that ChatGPT/Codex are optional adapters rather than required primary operators.

## Exact next packet

```text
Cortex Dual-Mode Replacement Readiness replay-backed primary-operator parity contract freeze
```

## Reusable knowledge

**RULE - Admission state is not execution state**

An accepted plan is eligible for operator dispatch; it is not evidence that execution occurred.

**PATTERN - Deterministic acceptance pair**

One acceptance identity and one correlated receipt make the pre-dispatch decision durable without creating a competing execution runtime.

**FAILURE MODE - Dry-run completion overclaim**

A safe admission decision is mistaken for proof of runtime dispatch or completed work.
