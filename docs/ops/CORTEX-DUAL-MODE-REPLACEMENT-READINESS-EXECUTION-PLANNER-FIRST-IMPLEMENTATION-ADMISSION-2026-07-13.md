# Cortex Dual-Mode Replacement Readiness Execution Planner First-Implementation Admission

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Scope: `admit the smallest safe future implementation slice for the deterministic advisory Cortex execution planner`
- Contract freeze: `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-EXECUTION-PLANNER-CONTRACT-FREEZE-2026-07-13.md`
- Registry: `docs/registry/CORTEX-EXECUTION-PLANNER-CONTRACT.v1.json`
- Branch basis: `main@2f2666b51e0b4b7c4ff71e340cc530b00baf8622`
- Remote parity at packet creation: `0 0`
- Marker movement: none
- Current marker: `Cortex Dual-Mode Replacement Readiness = 50%`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Runtime, queue, scheduler, Codex launch, and job execution: `none`

## Decision

Admit exactly one future implementation slice for a deterministic, advisory-only helper that consumes one validated synthesis packet, one compatible bridge candidate, and explicit durable root references. It returns one stable `atlas.cortex.execution_plan.v1` recommendation with job candidates, dependency waves, collision serialization, runtime recommendations, authority requirements, proof requirements, and `safe_to_admit`.

This packet admits implementation planning only. It does not implement or prove the planner, move a marker, create a queue, launch Codex, execute a job, mutate a repository or platform, write Discord, create an authoritative receipt, or widen authority.

## Exact Future Implementation Boundary

Admit exactly these two future changed paths:

- `ops/cortex/execution_planner.py`
- `tests/test_cortex_execution_planner.py`

No third committed implementation, fixture, schema, documentation, registry, package, runtime, owner-repo, or `_stack` path is admitted. Fixtures must be created inside the focused test or under ignored `tmp/atlas/**` paths.

## Future Helper Role And Authority Boundary

The helper may recommend admission only. `_stack` executes; Codex remains the native runtime; Atlas owns identity, contracts, receipts, markers, and routing; DiscordOS remains the sole logical board and Discord writer. The helper cannot execute, enqueue, dispatch, stage, commit, push, deploy, mutate cards, write Discord, access secrets, change markers, emit final authoritative receipts, or grant itself authority.

`Planning Does Not Grant Authority` is a governing rule for this slice. Full local access is a host capability recommendation and never implies push, deploy, production, secret, database, Discord, or other external mutation authority.

## Admitted CLI

The future worker may implement only:

```text
python ops/cortex/execution_planner.py
```

Admitted first-slice flags are:

- `--json`
- `--synthesis-packet <root-relative-json-path>`
- `--bridge-packet <root-relative-json-path>`
- repeatable `--source <root-relative-path>`
- `--output <root-relative-json-path>`
- `--strict`
- `--schema-only`

No network, execution, dispatch, auto-commit, provider-key, live-platform, queue, scheduler, or external-mutation flag is admitted. No file may be written without `--output`; output is allowed only under explicit `tmp/atlas/**.json` paths.

## Input, Trust, And Fail-Closed Rules

The future helper must require:

- synthesis schema exactly `atlas.cortex.chat_style_synthesis_packet.v1`;
- a safe/advisory synthesis packet with no blocker or invalidating conflict;
- bridge schema exactly `atlas.cortex.synthesis_execution_bridge_packet.v1`;
- an advisory bridge candidate that does not self-claim execution;
- preserved source digests and fail-closed digest conflicts;
- explicit root-relative references from admitted root truth classes;
- closeout/read-model evidence for resume or reconciliation planning; and
- known component ownership, marker truth, resource state, and authority.

It must reject absolute paths, parent traversal, `repos/**`, `secrets/**`, `runtime/**`, `.env*`, `.vercel`, `.codex`, archived transcripts, raw account/health/payment data, and live platform or network inputs. Hidden session inference and unrecorded transcripts are not durable truth.

Missing ownership, marker truth, resource state, authority, proof, or compatible source truth is a blocker. Stale or conflicted source truth, dependency cycles, collision ambiguity, unknown external mutation authority, unsupported execution classes, and attempts to self-grant authority fail closed.

## Deterministic Plan Contract

The future helper must emit the exact schema `atlas.cortex.execution_plan.v1` and preserve the frozen top-level field order from the registry:

1. `schema_version`
2. `plan_id`
3. `source_packet`
4. `source_digests`
5. `source_trust_classes`
6. `selected_lane`
7. `selected_marker`
8. `selected_packet`
9. `objective`
10. `plan_status`
11. `dependency_graph`
12. `execution_waves`
13. `job_candidates`
14. `project_component_ownership`
15. `runtime_recommendation`
16. `permission_posture`
17. `external_action_authority`
18. `scope_lock`
19. `resource_leases`
20. `verification_requirements`
21. `proof_requirements`
22. `commit_requirements`
23. `receipt_requirements`
24. `rollback_requirements`
25. `recovery_requirements`
26. `collision_risks`
27. `dependency_risks`
28. `required_approvals`
29. `blocked_reasons`
30. `skipped_reasons`
31. `next_recommended_packet`
32. `safe_to_admit`
33. `warnings`

Plan identity must derive from normalized admitted inputs and the frozen contract version, never wall-clock randomness. Source refs, candidates, dependency edges, waves, leases, risks, approvals, blockers, skipped reasons, and warnings must sort deterministically. Allowed plan statuses are only `draft`, `blocked`, and `ready_for_admission`; the helper cannot claim executed, running, verified, reconciled, completed, deployed, published, or failed-as-execution states.

## Job, Wave, And Runtime Rules

Every job candidate must have one independently verifiable outcome, stable ID, project/component/repository/owner, execution class (`read_only`, `repo_worktree`, or `canonical_workspace`), exact allowed and forbidden files or subsystem boundaries, dependency IDs, resource claims, provider/model/reasoning/speed recommendation, separated full-local-access and external-authority recommendations, verification/proof/commit/receipt/rollback/recovery contracts, approvals, blockers, skips, and risks.

Dependency edges are established before waves. Dependency cycles block admission. Jobs sharing files, generated outputs, schema ownership, canonical root, worktree, port, browser, or external writer are serialized into different waves. Read-only jobs may share a wave only when resource claims do not contend with active writers.

Runtime data is advisory and `_stack` must resolve and receipt effective policy later. Fast mode requires an explicit supported-model capability input; otherwise standard speed is recommended with a warning. Full local access never grants external mutation authority.

## Exit And Admission Policy

Top-level helper statuses and exits are:

- `ok`: exit `0`
- `advisory_gap`: exit `0`
- `conflict`: exit `0`, or exit `2` with `--strict`
- `blocker`: exit `2`
- `internal_error`: exit `3`

`safe_to_admit` is true only for `ready_for_admission` with no conflict, blocker, authority gap, cycle, collision ambiguity, stale truth, or unsupported execution class.

## Required Future Proof Matrix

The later worker must prove, at minimum:

1. deterministic, read-only schema-only output;
2. a valid synthesis/bridge pair producing a stable single-job plan;
3. deterministic waves for dependency-linked jobs;
4. fail-closed dependency cycles;
5. serialization for file, generated-output, canonical-root, port, browser, schema, and external-writer collisions;
6. sharing for non-contending read-only jobs;
7. blockers for missing/unknown ownership and unknown external authority;
8. fail-closed digest and stale/conflicted truth handling;
9. separation of full local access from external authority;
10. unsupported Fast fallback to standard with warning;
11. advisory-only runtime recommendations;
12. stable IDs and ordering for identical inputs;
13. absolute path, parent traversal, owner-repo, secret, runtime, transcript, and live-platform rejection;
14. output silence without `--output` and confinement to explicit `tmp/atlas/**.json`;
15. no subprocess, network, Git, marker, receipt, card, Discord, deploy, database, queue, scheduler, or owner-repo mutation path; and
16. strict conflict/blocker exits without adding a root validation error or warning.

## Frozen Future Verification Commands

The future worker must run exactly:

1. `python -m unittest tests.test_cortex_execution_planner -v`
2. `python ops/cortex/execution_planner.py --json --schema-only`
3. `python ops/cortex/execution_planner.py --json --synthesis-packet tmp/atlas/cortex-execution-planner-synthesis-fixture.json --bridge-packet tmp/atlas/cortex-execution-planner-bridge-fixture.json --source docs/registry/CORTEX-EXECUTION-PLANNER-CONTRACT.v1.json --output tmp/atlas/cortex-execution-plan-smoke.json`
4. `python ops/cortex/execution_planner.py --json --synthesis-packet tmp/atlas/cortex-execution-planner-conflict-synthesis.json --bridge-packet tmp/atlas/cortex-execution-planner-bridge-fixture.json --source docs/registry/CORTEX-EXECUTION-PLANNER-CONTRACT.v1.json --strict`
5. `python ops/validation/validate_stack.py`
6. `git diff --check`
7. `git status --short`
8. `git diff --name-only`

The test suite may generate ignored `tmp/atlas/**` fixtures immediately before smoke commands and may clean or safely retain them as disposable artifacts.

## Governance Findings

- `RULE - Planning Does Not Grant Authority`
- `PATTERN - Deterministic Plan Then Governed Admission`: Cortex emits one stable plan; a separate Atlas/`_stack` job admits and executes it.
- `FAILURE MODE - Advisory Plan Becomes Queue`: planner output must not become a durable scheduler or worker loop.
- `RULE - Resource Claims Before Parallelism`: execution waves follow dependency and resource collision checks.

## Continuity, Marker, And Blocker Decision

No marker moves. `Cortex Dual-Mode Replacement Readiness` remains `50%` because this packet admits but does not implement or prove the planner. The implementation is admitted but not landed.

The pre-existing root validation error `working-memory-catalog-drift` remains out of scope and must be preserved verbatim. This packet does not widen into runtime catalog repair or any owner-repo/platform work.

The exact next packet is:

```text
Cortex Dual-Mode Replacement Readiness execution planner prompt-pack and worker handoff contract
```

## Completion Boundary

This receipt is complete for the docs-only admission. No implementation file, test, fixture, schema, registry, package, runtime, queue, scheduler, owner-repo, platform, marker, Discord board, authoritative execution receipt, commit, or push is created by this packet.
