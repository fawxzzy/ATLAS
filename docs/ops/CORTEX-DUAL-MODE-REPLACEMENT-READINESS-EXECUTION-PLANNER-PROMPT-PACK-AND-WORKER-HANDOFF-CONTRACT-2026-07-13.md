Title: Cortex Dual-Mode Replacement Readiness execution planner prompt-pack and worker handoff contract
Commit Message: docs(cortex-planner): freeze worker handoff contract
Runtime Model: gpt-5.6-terra
Runtime Reasoning: high
Runtime Speed: standard
Runtime Permissions: full-access
Runtime Permission Profile: :danger-full-access
Runtime Approval Policy: never
Runtime Web Search Mode: disabled
Mutation Admission Path: docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-EXECUTION-PLANNER-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-13.md
Mutation Admission Path: docs/memory/initiatives/continuity-manifest-cortex-dual-mode-replacement-readiness.json
Mutation Admission Path: docs/atlas-book/05-receipt-index.md
Verify: python -m json.tool docs/memory/initiatives/continuity-manifest-cortex-dual-mode-replacement-readiness.json
Verify: python ops/validation/validate_stack.py
Verify: python ops/atlas/continuity_manifest_health.py
Verify: python ops/atlas/marker_aware_next_packet_planner.py --json
Verify: git diff --check

# Objective

Freeze the exact prompt pack and worker handoff for the first implementation of the deterministic advisory Cortex execution planner.

This is documentation-only. Do not implement the planner or tests, move markers, launch a child worker, mutate owner repos or platforms, or create execution infrastructure.

# Authority Sources

- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-EXECUTION-PLANNER-CONTRACT-FREEZE-2026-07-13.md`
- `docs/registry/CORTEX-EXECUTION-PLANNER-CONTRACT.v1.json`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-EXECUTION-PLANNER-FIRST-IMPLEMENTATION-ADMISSION-2026-07-13.md`
- current root baseline `main@8b508c1ac30300593426a50ac6d13f3788577d45`
- current root validation baseline `critical=0 error=0 warning=28 info=0`

# Exact Future Worker

Freeze one worker objective:

Implement `atlas.cortex.execution_plan.v1` as a deterministic, read-only-by-default advisory planner that validates one synthesis packet and one bridge candidate, produces stable job candidates and dependency waves, serializes resource collisions, recommends but never executes runtime policy, separates full local capability from external authority, and fails closed on stale/conflicting/unknown truth.

Future runtime recommendation:

- model: `gpt-5.6-terra`
- reasoning: `high`
- speed: `standard`
- permissions: `full-access`
- permission profile: `:danger-full-access`
- approval: `never`
- web search: `disabled`

The model choice is for the later implementation worker only. This documentation packet must not launch it.

# Exact Future Changed Paths

- `ops/cortex/execution_planner.py`
- `tests/test_cortex_execution_planner.py`

No third committed path. Test fixtures must be inline or generated under ignored `tmp/atlas/**`.

# Exact Future Unchanged Paths

- all existing `ops/cortex/**` files except the new `execution_planner.py`
- all existing `tests/**` files except the new focused test
- `docs/**`
- `packages/**`
- `repos/**`
- `_stack`
- `stack.yaml`
- `stack.lock.yaml`
- `runtime/**`
- `secrets/**`
- `.env*`

# Worker Input Contract

The worker must implement only these CLI flags:

- `--json`
- `--synthesis-packet`
- `--bridge-packet`
- repeatable `--source`
- `--output`
- `--strict`
- `--schema-only`

Required schemas:

- synthesis: `atlas.cortex.chat_style_synthesis_packet.v1`
- bridge: `atlas.cortex.synthesis_execution_bridge_packet.v1`
- output: `atlas.cortex.execution_plan.v1`

Inputs and outputs are root-relative. Outputs are explicit `tmp/atlas/**.json` only. No output flag means no write.

# Worker Behavior Contract

The worker must implement:

- stable plan IDs from normalized admitted inputs and contract version;
- the exact top-level field order from the contract registry;
- deterministic list and graph ordering;
- plan statuses `draft`, `blocked`, and `ready_for_admission` only;
- one independently verifiable outcome per job candidate;
- dependency cycle detection;
- deterministic execution-wave assignment after dependency validation;
- serialization for overlapping files, generated artifacts, schemas, canonical root, worktrees, ports, browsers, and external writers;
- same-wave admission only for non-contending read-only candidates;
- execution classes `read_only`, `repo_worktree`, and `canonical_workspace`;
- runtime recommendation for provider/model/reasoning/speed/permissions/fallback;
- Fast capability fallback to standard with warning;
- separate external-action authority and required approvals;
- prospective verification, proof, commit, receipt, rollback, and recovery requirements;
- explicit blockers, skipped reasons, collision risks, and dependency risks;
- `safe_to_admit` only for conflict-free `ready_for_admission` output.

# Worker Denials

The implementation and helper must contain no path that:

- invokes Codex, `_stack`, subprocesses, network clients, platform tools, or shell commands;
- schedules, queues, leases, dispatches, retries, or supervises actual work;
- stages, commits, pushes, opens PRs, deploys, writes cards, mutates Discord, changes databases, or accesses secrets;
- reads hidden transcripts, owner repo source, runtime state, `.env*`, browser profiles, or live platforms;
- moves markers or writes final authoritative receipts;
- creates a custom SQLite queue, worker loop, scheduler, or replacement runtime.

# Exact Proof Matrix

The future worker completion proof must map each item to literal source/test evidence:

1. deterministic schema-only output;
2. stable single-job plan from valid fixtures;
3. deterministic multi-job dependency waves;
4. cycle blocker;
5. file collision serialization;
6. generated-artifact collision serialization;
7. schema and canonical-root collision serialization;
8. worktree, port, browser, and external-writer collision serialization;
9. non-contending read-only parallel wave;
10. missing ownership blocker;
11. source digest conflict blocker;
12. stale/conflicted truth blocker;
13. unknown external authority blocker;
14. full local capability separated from external authority;
15. unsupported Fast fallback warning;
16. advisory runtime recommendation only;
17. deterministic IDs and ordering across repeated runs;
18. invalid synthesis schema rejection;
19. invalid bridge schema rejection;
20. absolute path rejection;
21. parent traversal rejection;
22. owner-repo/secret/runtime/transcript/live-platform source rejection;
23. no output without `--output`;
24. only `tmp/atlas/**.json` output admitted;
25. strict conflict exit 2;
26. blocker exit 2 and internal error exit 3;
27. no subprocess/network/execution imports or calls;
28. no Git/marker/receipt/card/platform/queue/scheduler mutation;
29. exact two-file diff;
30. validation does not exceed baseline `0/0/28/0`.

# Exact Future Verification

Run in this order:

1. `python -m unittest tests.test_cortex_execution_planner -v`
2. `python ops/cortex/execution_planner.py --json --schema-only`
3. `python ops/cortex/execution_planner.py --json --synthesis-packet tmp/atlas/cortex-execution-planner-synthesis-fixture.json --bridge-packet tmp/atlas/cortex-execution-planner-bridge-fixture.json --source docs/registry/CORTEX-EXECUTION-PLANNER-CONTRACT.v1.json --output tmp/atlas/cortex-execution-plan-smoke.json`
4. `python ops/cortex/execution_planner.py --json --synthesis-packet tmp/atlas/cortex-execution-planner-conflict-synthesis.json --bridge-packet tmp/atlas/cortex-execution-planner-bridge-fixture.json --source docs/registry/CORTEX-EXECUTION-PLANNER-CONTRACT.v1.json --strict`
5. `python ops/validation/validate_stack.py`
6. `python ops/atlas/continuity_manifest_health.py`
7. `git diff --check`
8. `git status --short`
9. `git diff --name-only`

The focused test may create the ignored smoke fixtures. The strict-conflict smoke is expected to exit 2; the worker must record that as proof, not misreport it as an unexpected failure.

# Completion And Receipt Requirements

The future worker must return:

- implementation status;
- exact changed paths;
- test count and failures;
- smoke status, schema, plan ID, plan status, wave count, job count, and `safe_to_admit`;
- strict conflict exit code;
- validation baseline comparison;
- no-execution/no-external-mutation confirmation;
- blockers and risks;
- commit SHA when runner-owned commit succeeds;
- exact next packet: worker-cluster reconciliation.

It must write `_stack`'s required commit metadata and spec-to-diff artifact, stage only the two admitted files, and leave push to parent review.

# Reusable Governance

- `RULE - Worker Contracts Precede Worker Launch`: exact inputs, outputs, files, proofs, and authority are frozen before implementation starts.
- `PATTERN - Advisory Planner, Governed Executor`: Cortex plans; `_stack` admits and executes separately.
- `FAILURE MODE - Planner Runtime Creep`: planning code gains subprocess, network, queue, scheduler, or external-writer behavior.
- `RULE - Validation Baseline Is A Budget`: a bounded implementation cannot add root errors or warnings.

# Marker Decision

No marker moves. `Cortex Dual-Mode Replacement Readiness` remains `50%`.

# Exact Next Packet

Advance only to:

`Cortex Dual-Mode Replacement Readiness execution planner implementation-readiness closeout and worker routing`

# Continuity Update

Update the manifest surgically to add this receipt to maintained receipt and owner-truth surfaces, preserve marker 50 and unrelated history, advance the next package to the exact readiness closeout above, set freshness to `execution-planner-prompt-pack-current`, and state that the worker contract is frozen but no implementation is landed.

# Receipt Index

Add one relative link for the new prompt-pack receipt without reordering unrelated history.

# Expected Changed Paths

- docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-EXECUTION-PLANNER-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-13.md
- docs/memory/initiatives/continuity-manifest-cortex-dual-mode-replacement-readiness.json
- docs/atlas-book/05-receipt-index.md

# Expected Unchanged Paths

- docs/registry/CORTEX-EXECUTION-PLANNER-CONTRACT.v1.json
- docs/atlas-book/01-current-state.md
- docs/atlas-book/02-lanes-and-markers.md
- ops/cortex/**
- tests/**
- packages/**
- repos/**
- stack.yaml
- stack.lock.yaml
- runtime/**
- secrets/**

# Acceptance Criteria

- [ac-01] The prompt-pack document contains the exact two future paths, `gpt-5.6-terra`, `Worker Contracts Precede Worker Launch`, and the numbered literal `30. validation does not exceed baseline`.
- [ac-02] The continuity-manifest diff contains the exact next-package literal `Cortex Dual-Mode Replacement Readiness execution planner implementation-readiness closeout and worker routing` and the freshness literal `execution-planner-prompt-pack-current`.
- [ac-03] The receipt-index diff contains the exact filename `CORTEX-DUAL-MODE-REPLACEMENT-READINESS-EXECUTION-PLANNER-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-13.md`.

# Blocked/Skipped Reporting Rules

- Stop on pre-existing changes to admitted paths.
- If the preserved prompt conflicts with current committed source truth, report the conflict instead of guessing.
- Do not cite unchanged literals as spec-to-diff evidence.
- Do not bypass exact-path admission or spec-to-diff.
- Preserve all unrelated untracked worktrees and user artifacts.

# Completion Artifact

Write UTF-8 JSON to `.codex/spec-to-diff-proof.json` with one exact changed supporting path per criterion and short literal evidence present in that path's final diff. Each criterion must cite exactly one changed path. Run `pnpm run codex:spec-to-diff:preflight` and correct the proof artifact until the command exits successfully.

# Return Contract

Return status, commit SHA, exact changed paths, validations, spec-to-diff result, marker decision, prohibited actions, blockers, and next packet. Do not push.
