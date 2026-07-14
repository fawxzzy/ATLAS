# Cortex Dual-Mode Replacement Readiness Replay/Evaluation Harness Marker-Surface Ratchet Decision

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only marker-surface ratchet decision`
- Branch basis: `main@5b4394c8`
- Owner-repo mutation: `none`
- Platform mutation: `none`

## Decision

`Cortex Dual-Mode Replacement Readiness` moves from `60%` to `70%`.

The published threshold model names:

- `70%`: replay/evaluation harness compares Chat/Codex outputs against Cortex outputs

That threshold is now satisfied by:

- `ops/cortex/replay_evaluation_harness.py`
- `tests/test_cortex_replay_evaluation_harness.py`
- implementation commit `75a714e746a784306ae10c19b14006b401a3e343`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-REPLAY-EVALUATION-HARNESS-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-13.md`
- reconciliation commit `5b4394c8`

## Why This Is A Real Ratchet

Executed state changed. Atlas now has a deterministic offline comparator that accepts explicit Chat/Codex-style adapter candidates plus Cortex synthesis and execution-plan artifacts, normalizes only rubric-admitted contract dimensions, reports constraint equivalence or strictness, detects regressions and authority widening, and emits a stable advisory report.

The harness remains advisory. It cannot inspect hidden conversations, call models, launch Codex, invoke `_stack`, execute Git, create queues or schedulers, write final receipts, move markers, mutate owner repositories, or perform external actions.

## Proof Basis

- focused tests: `32/32` passing
- schema: `atlas.cortex.replay_evaluation_report.v1`
- schema-only result: `blocked`
- schema-only safe-to-use: `false`
- deterministic repeated output: proved
- prior-report regression detection: proved
- strict regression, incomparable, and blocked exits: `2`
- runner mutation scope: exact two files
- runner spec-to-diff: passed
- ordinary stack validation: `critical=0 error=0 warning=28 info=0`, matching the admitted baseline
- continuity health: `23/23 ok`, zero warnings, zero errors
- implementation remote parity: `origin/main...main = 0 0`
- reconciliation remote parity: `origin/main...main = 0 0`

## Marker Decision

`Cortex Dual-Mode Replacement Readiness` moves from `60%` to `70%`.

No other marker moves.

## Boundaries Preserved

- Atlas remains identity, contract, receipt, marker, and routing authority.
- `_stack` remains the execution/operator plane.
- Codex remains the native execution runtime.
- DiscordOS remains the sole logical board and Discord writer.
- Cortex remains deterministic and advisory only.
- No owner repo, platform, deployment, secret, workflow, card, Discord, Vercel, Supabase, or GitHub external surface was mutated.
- No custom SQLite execution queue, worker loop, or scheduler was created.

## Exact Next Packet

`Cortex Dual-Mode Replacement Readiness first ATLAS lane Cortex-assisted bridge contract freeze`

The next published milestone is:

- `80%`: one ATLAS lane planned or executed with Cortex-assisted bridge

No first-lane bridge execution is claimed in this ratchet.

