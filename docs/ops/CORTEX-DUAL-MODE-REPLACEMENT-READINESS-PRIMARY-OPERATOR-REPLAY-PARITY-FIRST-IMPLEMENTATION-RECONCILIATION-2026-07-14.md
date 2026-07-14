# Cortex Dual-Mode Replacement Readiness primary-operator replay parity first implementation reconciliation

- Date: `2026-07-14`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `root-owned deterministic offline replay parity`
- Marker movement: none; remains `90%`

## Executed state

The first replay-parity implementation is landed in:

- `ops/cortex/primary_operator_replay_parity.py`
- `tests/test_cortex_primary_operator_replay_parity.py`

It builds the internal primary-operator acceptance/receipt baseline and optionally compares one explicit ChatGPT/Codex-style adapter projection without requiring that adapter.

## Proven behavior

- internal no-adapter replay produces a complete safe baseline;
- identical inputs produce stable report identities;
- equivalent optional adapter projections pass;
- stricter adapter projections remain safe;
- Cortex-stricter outcomes are classified and held rather than treated as parity;
- external-authority widening, dispatch claims, mutation claims, and `_stack` replacement are authority regressions;
- plan and receipt-correlation mismatches fail closed;
- output is restricted to explicit `tmp/atlas/**.json` paths;
- the report never claims runtime dispatch or mutation.

Focused proof: `11` tests passed.

Combined Cortex and selector proof: `148` tests passed.

## Architecture result

ChatGPT and Codex are now proven optional at the acceptance/replay layer. Cortex can produce the governed baseline without either adapter, and adapter projections cannot silently broaden authority.

This does not yet prove execution. `_stack` remains the only admitted local operator plane.

## Marker decision

The marker remains `90%`.

The parity gap is closed, but `100%` still requires one bounded real dispatch through `_stack`, a durable result correlated to the primary-operator acceptance identity, and a final independent endgame audit.

## Exact next packet

```text
Cortex Dual-Mode Replacement Readiness _stack dispatch and durable result contract freeze
```

## Reusable knowledge

**RULE - Parity proof must include no-adapter operation**

An external surface is optional only when the internal system can produce the complete governed result without it.

**PATTERN - Authority-aware replay projection**

Compare stable identities, decision state, reasons, operator ownership, dispatch flags, and receipt correlation rather than comparing prose.

**FAILURE MODE - Equivalent text, weaker authority**

An adapter summary looks equivalent while omitting blockers or claiming actions the internal operator denied.
