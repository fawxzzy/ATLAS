# Cortex Dual-Mode Replacement Readiness Replay/Evaluation Harness Prompt-Pack And Worker Handoff Contract

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only worker handoff contract`
- Marker movement: `none`
- Worker launch: `none`

## Worker Objective

Implement the first deterministic offline replay/evaluation harness in exactly:

- `ops/cortex/replay_evaluation_harness.py`
- `tests/test_cortex_replay_evaluation_harness.py`

The worker must consume the frozen registry, compare explicit normalized adapter and Cortex artifacts, emit `atlas.cortex.replay_evaluation_report.v1`, and remain advisory only.

## Runtime Route

- model: `gpt-5.6-terra`
- reasoning: `high`
- speed: `standard`
- permissions: `full-access`
- permission profile: `:danger-full-access`
- approval: `never`
- web search: `disabled`
- execution class: `canonical_workspace`
- push: `manual-only`

## Required CLI

The implementation must provide:

- `--json`;
- `--schema-only`;
- explicit case, adapter, synthesis, plan, and rubric paths;
- optional prior-report path;
- optional explicit `--output`;
- `--strict`.

Inputs must be admitted root-relative paths. Output must be an explicit `tmp/atlas/**.json` path.

## Verification

Run:

```text
python -m unittest tests.test_cortex_replay_evaluation_harness -v
python -m py_compile ops/cortex/replay_evaluation_harness.py tests/test_cortex_replay_evaluation_harness.py
python ops/cortex/replay_evaluation_harness.py --json --schema-only
python ops/validation/validate_stack.py
python ops/atlas/continuity_manifest_health.py
git diff --check
git diff --name-only
```

Focused fixtures may be created only under ignored `tmp/atlas/**` and must not become committed source truth.

## Diff-Addressable Acceptance Criteria

1. Source contains `REPORT_SCHEMA = "atlas.cortex.replay_evaluation_report.v1"` and explicit no-execution authority literals.
2. Source contains all seven result-class literals: `equivalent`, `cortex_stricter`, `adapter_stricter`, `complementary`, `regression`, `incomparable`, `blocked`.
3. Tests contain literal equivalent, digest-conflict, authority-regression, deterministic-output, prior-report-regression, and safe-output cases.
4. Tests contain literal hidden-transcript, secret, absolute, traversal, owner-repo, runtime, live-platform, and no-output-without-flag guards.

Each criterion must cite one exact changed file and literal final-diff evidence.

## Prohibited Actions

No direct implementation outside `_stack`; no third file; no existing helper changes; no model/network/subprocess/Git/Codex/queue/scheduler/marker/card/platform path; no owner repo; no push before parent review.

## Completion Contract

Return exact changed paths, focused test count, schema-only result, smoke comparison result, strict exit behavior, validation comparison, spec-to-diff result, commit SHA, authority-denial confirmation, blockers, and the exact reconciliation packet.

## Marker Decision

No marker moves. The lane remains `60%`.

## Exact Next Packet

`Cortex Dual-Mode Replacement Readiness replay/evaluation harness implementation-readiness closeout and worker routing`

