# Cortex Dual-Mode Replacement Readiness Execution Planner Marker-Surface Ratchet Decision

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only marker-surface ratchet decision`
- Branch basis: `main@0a82fb2f`
- Owner-repo mutation: `none`
- Platform mutation: `none`

## Decision

`Cortex Dual-Mode Replacement Readiness` moves from `50%` to `60%`.

The published threshold model names:

- `60%`: execution planner can route bounded packets from Cortex state

That threshold is now satisfied by:

- `ops/cortex/execution_planner.py`
- `tests/test_cortex_execution_planner.py`
- implementation commit `9285757383adb7711b0139eb38e1e3d827aabd99`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-EXECUTION-PLANNER-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-13.md`
- reconciliation commit `0a82fb2f`

## Why This Is A Real Ratchet

Executed state changed. Atlas now has a deterministic, implementation-backed planner that consumes admitted Cortex synthesis and bridge packets, normalizes bounded job candidates, validates ownership and dependencies, detects conflicts and stale truth, assigns serialized or parallel execution waves from resource claims, and emits an explicit admission recommendation.

The planner remains advisory. It cannot launch Codex, invoke `_stack`, execute Git, create a queue or scheduler, write a final receipt, move a marker, mutate an owner repository, or perform an external action. Full local capability remains separate from external-action authority.

## Proof Basis

- focused tests: `39/39` passing
- schema: `atlas.cortex.execution_plan.v1`
- schema-only status: `draft`
- schema-only admission: `safe_to_admit=false`
- valid single-job smoke: `ready_for_admission`, one job, one wave, `safe_to_admit=true`
- strict conflict exit: `2`
- runner mutation scope: exact two files
- runner spec-to-diff: passed
- ordinary stack validation: `critical=0 error=0 warning=28 info=0`, matching the admitted baseline
- continuity health: `23/23 ok`, zero warnings, zero errors
- remote parity before this decision: `origin/main...main = 0 0`

## Marker Decision

`Cortex Dual-Mode Replacement Readiness` moves from `50%` to `60%`.

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

`Cortex Dual-Mode Replacement Readiness replay/evaluation harness contract freeze`

The next published milestone is:

- `70%`: replay/evaluation harness compares Chat/Codex outputs against Cortex outputs

No replay harness implementation is claimed in this ratchet.

