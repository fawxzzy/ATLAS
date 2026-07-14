# Cortex Dual-Mode Replacement Readiness Replay/Evaluation Harness First-Implementation Admission

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Root baseline: `main@ff63d215`
- Marker movement: `none`
- Implementation: `none`

## Decision

Admit one future deterministic offline replay/evaluation harness implementation.

Exact future changed paths:

- `ops/cortex/replay_evaluation_harness.py`
- `tests/test_cortex_replay_evaluation_harness.py`

Both paths are absent at admission. No third committed path is admitted.

## Governing Contract

- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-REPLAY-EVALUATION-HARNESS-CONTRACT-FREEZE-2026-07-13.md`
- `docs/registry/CORTEX-REPLAY-EVALUATION-HARNESS-CONTRACT.v1.json`

The worker must implement `atlas.cortex.replay_evaluation_report.v1` as an offline, deterministic, advisory-only comparator over explicit normalized artifacts.

## Required Proof

The worker must cover the sixteen proof obligations frozen by the contract, including equivalent, stricter, complementary, regression, incomparable, and blocked cases; source and path guards; authority-regression handling; deterministic output; prior-report comparison; explicit-output behavior; strict exits; and no execution or platform side effects.

The minimum focused suite must include literal tests for:

- equivalent normalized artifacts;
- adapter and Cortex constraint omissions;
- authority widening regression;
- digest conflict blocker;
- hidden transcript, secret, absolute, traversal, owner-repo, runtime, and live-platform rejection;
- deterministic repeated output;
- prior-report regression;
- safe explicit `tmp/atlas/**.json` output;
- no output without `--output`;
- strict nonzero behavior.

## Authority Boundary

No implementation may call a model, launch Codex, invoke `_stack`, execute Git, scrape a transcript, access a secret, create a queue or scheduler, move a marker, write a final receipt, mutate an owner repo, or query/mutate a live platform.

## Stop Conditions

Stop if implementation requires a third file, existing helper modification, hidden transcript access, subjective model scoring, network access, owner-repo access, runtime authority, or external mutation.

## Marker Decision

No marker moves. The lane remains `60%`.

## Exact Next Packet

`Cortex Dual-Mode Replacement Readiness replay/evaluation harness prompt-pack and worker handoff contract`

