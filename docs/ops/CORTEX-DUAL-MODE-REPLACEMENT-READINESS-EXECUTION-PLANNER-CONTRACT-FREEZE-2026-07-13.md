# Cortex Dual-Mode Replacement Readiness Execution Planner Contract Freeze

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only deterministic advisory planner contract freeze`
- Scope: `freeze the first planner-output doctrine between validated Cortex synthesis/bridge candidates and _stack admission`
- Branch basis: `main@99404c72a23fb28358815c0a5afa60335437af85`
- Marker movement: none
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Runtime, queue, scheduler, Codex launch, and job execution: `none`

## Decision

Adopt this future planner-output schema identifier:

```text
atlas.cortex.execution_plan.v1
```

This is a machine-readable doctrine contract, not a runtime-adopted implementation schema. The future execution planner is deterministic and advisory-only: it converts one validated synthesis packet and one compatible bridge candidate plus durable root truth into one bounded plan. It never launches Codex, executes a job, creates a queue or scheduler, mutates a repository or platform, creates a receipt, moves a marker, or claims final authority.

The responsibility split is frozen:

- Cortex recommends one job or a dependency-ordered set of non-overlapping job candidates.
- `_stack` remains the execution and operator plane.
- Codex remains the native execution runtime.
- Atlas remains authority for identity, contracts, receipts, markers, and routing.
- DiscordOS remains the sole logical board and Discord writer.
- External mutation authority remains explicit, task-local, and separately evaluated by `_stack`.

`safe_to_admit` is an admission recommendation only. It is distinct from safe to execute and is never execution authority.

## Admitted Inputs

The planner accepts only explicit, root-owned inputs in deterministic reference order:

1. exactly one `atlas.cortex.chat_style_synthesis_packet.v1` packet;
2. exactly one compatible `atlas.cortex.synthesis_execution_bridge_packet.v1` candidate;
3. current continuity-manifest and marker-source references;
4. component and topology references;
5. applicable Playbook doctrine references;
6. prior closeout read-model evidence when work is resumed or reconciled;
7. operator intent and an explicit authority envelope;
8. optional card and job correlation identifiers; and
9. resource state supplied through durable receipts only.

The planner must not use hidden session inference, browser/tab state, local absolute paths as durable truth, secrets, `.env*`, live-platform reads, or an unrecorded transcript. It must reject secret-bearing inputs rather than redact and continue.

## Deterministic Plan Shape

Every future `atlas.cortex.execution_plan.v1` output preserves this top-level field order:

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

Plan identity is the stable digest of the admitted, normalized inputs and this frozen contract version. Identical admitted inputs must produce identical `plan_id`, job IDs, dependency edges, waves, arrays, and object-key order. References sort by normalized repository-relative path, then stable identifier. Job candidates sort by stable job ID after graph validation; execution waves sort numerically, then by job ID.

## Required Output Semantics

- `source_packet`, `source_digests`, and `source_trust_classes` preserve the selected synthesis/bridge identities, normalized digests, and durable/advisory trust class without inventing proof.
- `selected_lane`, `selected_marker`, `selected_packet`, `objective`, and `plan_status` describe one selected scope. Allowed `plan_status` values are `draft`, `blocked`, and `ready_for_admission`; a plan cannot claim `executed`, `verified`, `reconciled`, or `completed`.
- `dependency_graph` records directed prerequisite edges before `execution_waves` are assigned. A cycle blocks admission.
- Every `job_candidate` has a stable ID, one independently verifiable outcome, project/component and repository owner, allowed and forbidden paths/subsystems, and one execution class: `read_only`, `repo_worktree`, or `canonical_workspace`.
- `runtime_recommendation` may recommend provider, model, reasoning, speed, capability checks, and fallback. `_stack` must resolve and receipt the effective runtime at execution time. Fast mode must be capability-detected for the selected model; unsupported fast mode degrades to standard with an explicit warning.
- `permission_posture` states host capability only. Full local access does not grant deploy, push, Discord, database, secret, production, or any external action authority.
- `external_action_authority` is separate and task-local. Its default is `no_execution_authority`; it cannot be elevated by planner output.
- `scope_lock` names exact allowed and forbidden paths or subsystems. Absolute paths, traversal paths, generated-output paths outside explicit `tmp/atlas/**.json`, broad staging, cleanup, and mutation outside the selected scope are rejected.
- `resource_leases` reserve files, worktrees, ports, browsers, schemas, canonical root, and external writers from durable receipt-backed resource state. A planner cannot fabricate a lease.
- Verification, proof, commit, receipt, rollback, and recovery requirements are future execution requirements only; the plan cannot claim that they occurred.
- `collision_risks`, `dependency_risks`, `required_approvals`, `blocked_reasons`, `skipped_reasons`, and `next_recommended_packet` remain explicit even for a blocked plan.

## Planning Rules

1. One independently verifiable outcome is required for every job candidate.
2. Dependency edges are established before execution-wave assignment.
3. Jobs with overlapping files, generated artifacts, schema ownership, canonical-workspace ownership, persistent-browser ownership, or Discord-writer ownership must not parallelize.
4. Read-only work may parallelize only when it cannot contend with the root writer or owner writer.
5. Model routing is a recommendation that `_stack` resolves and receipts at execution time.
6. Fast mode is capability-detected for the selected model and degrades to standard with an explicit warning when unavailable.
7. Full local access is host capability, not deploy, push, Discord, database, secret, or production authority.
8. Vercel production mutation remains separately current-thread approved for each named project.
9. Existing dirty paths and user work are preserved; planner output cannot authorize broad staging or cleanup.
10. A plan may be `draft`, `blocked`, or `ready_for_admission` only; it cannot claim execution or final truth.
11. Identical admitted inputs produce stable plan identity and ordering.
12. No custom SQLite execution queue, worker loop, or scheduler is introduced by this contract.

## Failure-Closed Admission

The planner sets `safe_to_admit=false` and emits a deterministic blocked reason when any of the following is true:

- source schemas are missing or invalid;
- source digests conflict;
- selected source truth is stale or marker sources conflict;
- an owner is unknown;
- Git state is unsafe without an admitted repair packet;
- files, generated artifacts, schemas, worktrees, ports, browsers, canonical root, or external writers overlap;
- external authority is unknown;
- the requested execution class is unavailable;
- runtime selection is unsupported and has no admissible fallback;
- an input bears a secret;
- the plan depends on a hidden transcript or hidden session inference;
- scope spans multiple lanes without an approved cross-repo packet; or
- the plan attempts to grant itself execution, final-receipt, marker, routing, Discord-writer, or external-mutation authority.

Missing required proof, unknown authority, stale packets, and active-writer overlap are not warnings: they are blocking admission conditions.

## First Implementation Boundary

The future first implementation is limited exactly to:

- `ops/cortex/execution_planner.py`
- `tests/test_cortex_execution_planner.py`

It may read existing synthesis-generator output and the bridge contract. It must not modify existing Cortex helpers, `_stack`, owner repositories, Atlas Contracts, DiscordOS, cards, live platforms, secrets, markers, or runtime state. It may write only explicit `tmp/atlas/**.json` outputs.

Required proof for that future admission includes deterministic IDs/order, valid single-job planning, dependency waves, collision serialization, fail-closed authority conflicts, Git/resource conflict handling, runtime recommendation and fallback warnings, absolute/traversal/output-path rejection, no execution side effects, strict-mode exit behavior, and output confinement to `tmp/atlas/**.json`.

## Marker Decision

No marker moves.

`Cortex Dual-Mode Replacement Readiness` remains `50%`. This packet freezes doctrine only; it does not admit, implement, reconcile, or adopt the execution planner threshold. Movement above `50%` remains blocked until planner implementation is admitted, implemented, proof-backed, reconciled, and separately ratcheted.

## Exact Next Packet

```text
Cortex Dual-Mode Replacement Readiness execution planner first-implementation admission
```

## Prohibited Actions Confirmed

This packet did not implement the planner, execute jobs, launch Codex, create a queue or scheduler, mutate owner repositories, query live platforms, move a marker, or claim final authority.
