# ATLAS Lifeline Wave 1 Launch

This document turns the Lifeline restart posture into concrete repo-scoped worker handoffs.

Use it with `docs/ops/ATLAS-LIFELINE-PLATFORM-RESTART.md`. The restart document stays the posture anchor. This document is the launch packet for the first execution wave.

## Scope

Launch now:

- `W0` stack hygiene
- `W1` Lifeline runtime foundation
- `W2` Lifeline deploy contract
- `W3` Lifeline ops baseline
- `W5` Playbook shadow codification

Selected pilot lane:

- `W4` pilot app migration -> `trove`

Atlas remains coordination-only in this phase. Do not open an Atlas execution lane.

## Launch Order

1. freeze the restart posture slice unchanged
2. land `W0` to reduce validator noise without reopening strategy
3. run `W1`, `W2`, `W3`, and `W5` in parallel
4. start `W4` against `trove` only after `W0` lands and `W1` plus `W2` are stable enough to support a real migration

## Worker Map

| Worker | Lane | Owner repo(s) | Status | Depends on |
| --- | --- | --- | --- | --- |
| `W0` | stack hygiene | `stack`, `trove` | ready | none |
| `W1` | runtime foundation | `lifeline` | ready | none |
| `W2` | deploy contract | `lifeline` | ready | none |
| `W3` | ops baseline | `lifeline` | ready | none |
| `W4` | pilot app migration | `trove` | queued | `W0`, `W1`, `W2` |
| `W5` | Playbook shadow codification | `playbook` and optional stack links | ready | none |

## Packet Layout

Worker prompts and assignment templates live under:

- `runtime/atlas/context-packs/wave-1-lifeline-launch/`

Deterministic context refs for the ready workers live under:

- `runtime/atlas/context-packs/wave-1-lifeline-launch-w0-stack-hygiene/`
- `runtime/atlas/context-packs/wave-1-lifeline-launch-w1-runtime-foundation/`
- `runtime/atlas/context-packs/wave-1-lifeline-launch-w2-deploy-contract/`
- `runtime/atlas/context-packs/wave-1-lifeline-launch-w3-ops-baseline/`
- `runtime/atlas/context-packs/wave-1-lifeline-launch-w4-trove-pilot/`
- `runtime/atlas/context-packs/wave-1-lifeline-launch-w5-playbook-shadow/`

## Active Rules

- keep worker ownership non-overlapping
- do not touch unrelated Atlas UI observe drift from this launch packet
- do not change `docs/ops/ATLAS-LIFELINE-PLATFORM-RESTART.md` from hygiene or repo-execution workers
- do not move platform implementation truth into the stack root
- keep Vercel available as fallback until the pilot parity and rollback rehearsal are real

## Wave 1 Done Criteria

Call the milestone hit only when:

- Trove deploys through Lifeline
- health and logs are visible
- rollback is rehearsed
- the parity checklist is explicit
- Vercel is no longer the required runtime for Trove

## Pilot Selection

The selected pilot app repo for `W4` is `trove`.

Operational rules for this handoff:

- `W0` must land before `W4` because both lanes would otherwise contend around `repos/fawxzzy-trove/.codex/config.toml`
- `W4` stays inside `trove` only; if a paired Lifeline change becomes unavoidable, open a new non-overlapping follow-on slice instead of widening the pilot worker

## References

- posture anchor: `docs/ops/ATLAS-LIFELINE-PLATFORM-RESTART.md`
- initiative: `docs/memory/initiatives/initiative-lifeline-platform-cutover.json`
- plan: `docs/memory/plans/wave-1-lifeline-platform-cutover.json`
- launch manifest: `runtime/atlas/context-packs/wave-1-lifeline-launch/launch.manifest.json`
