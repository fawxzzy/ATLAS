# Cortex Dual-Mode Replacement Readiness - Second ATLAS Lane 90 Percent Marker Decision

## Decision

`Cortex Dual-Mode Replacement Readiness` moves from `80%` to `90%`.

The governing admission receipt publishes the threshold: `90%: multiple lanes use the Cortex bridge safely.` This decision changes only that marker. `Atlas Full-System Re-evaluation` remains `50%`, and `Root Path Hygiene` remains `100%`.

## Independent Evidence

1. **Atlas Contracts v2 Cluster 2** used the deterministic advisory bridge `docs/registry/ATLAS-CONTRACTS-V2-CLUSTER-2-CORTEX-BRIDGE.v1.json` with plan `plan-967699c7442b4efd716c`. `_stack` producer adoption commit `59c984c66fedf2ccb00ffb47fb92ea9f8cb990f8` and Atlas consumer adoption commit `c4c2b2acfc97b86e24541cd9e390d4475ba3924c` provide producer/consumer proof for six of eleven v2 contract families. Planning evidence is `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-FIRST-ATLAS-LANE-CORTEX-ASSISTED-BRIDGE-PLANNING-PROOF-2026-07-13.md`.
2. **Root Path Hygiene** used the distinct deterministic advisory bridge `docs/registry/ROOT-PATH-HYGIENE-CORTEX-BRIDGE.v1.json` with plan `plan-07dfe809d062b89cafde`. Its three planned jobs were executed through Atlas/Codex and `_stack` under existing authority boundaries: owner remediation commit `32f9205013bbb84e19153261b1aab2c0ada975d4` and final Atlas reconciliation commit `d1555d57`. `docs/ops/ROOT-PATH-HYGIENE-EXECUTION-RECONCILIATION-2026-07-13.md` records the fixed historical denominator `25`, accepted `25`, pending `0`, and `complete: true`; sixteen preserved historical findings and three newer findings remain explicitly scoped.

These lanes are distinct in selected lane, bridge artifact, plan, job set, execution boundary, and reconciliation result. Their evidence satisfies the published 90 percent threshold without treating either planning proof as execution by Cortex.

## Authority And Health Posture

Cortex supplied deterministic advisory synthesis-to-execution planning only. Cortex did not execute, commit, push, approve, operate owner repositories, issue final receipts, or move markers. Atlas/Codex and `_stack` performed the admitted execution and reconciliation; Atlas remains the marker and final-receipt authority.

This decision denies any expansion of owner-repo, external-platform, board, deployment, secret, queue, scheduler, or final-receipt authority. Current validation is not globally clean: it records one separately tracked stack-lock error and 19 classified root-path warnings. That validation debt is separate from this marker movement.

## Why 100 Percent Is Not Met

The unchanged requirement is: `100%: ChatGPT/Codex are optional external adapters, not required primary operators.` The current bridge still depends on Atlas/Codex and `_stack` for admitted execution and reconciliation. An internal Cortex primary-operator path, durable acceptance/receipt behavior, and replay-backed parity have not yet been proven. Another planning-only lane would not satisfy that endgame.

## Governing References

- `docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-FIRST-ATLAS-LANE-CORTEX-ASSISTED-BRIDGE-PLANNING-PROOF-2026-07-13.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-SECOND-ATLAS-LANE-ROOT-PATH-HYGIENE-PLANNING-PROOF-2026-07-13.md`
- `docs/ops/ROOT-PATH-HYGIENE-EXECUTION-RECONCILIATION-2026-07-13.md`
