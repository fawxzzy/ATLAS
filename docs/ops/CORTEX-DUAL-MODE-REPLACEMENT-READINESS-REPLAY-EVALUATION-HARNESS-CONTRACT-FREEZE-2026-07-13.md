# Cortex Dual-Mode Replacement Readiness Replay/Evaluation Harness Contract Freeze

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only contract freeze`
- Root baseline: `main@4dc69040`
- Marker movement: `none`
- Implementation: `none`
- Owner-repo mutation: `none`
- Platform mutation: `none`

## Decision

Freeze the first deterministic replay/evaluation contract for comparing explicit Chat/Codex adapter artifacts with explicit Cortex artifacts.

The future harness is an offline, advisory comparator. It does not retrieve hidden conversations, infer private reasoning, call a model, execute a plan, select authoritative project truth, launch Codex, invoke `_stack`, move a marker, publish a result, or mutate an owner repository or external platform.

Machine-readable doctrine:

- `docs/registry/CORTEX-REPLAY-EVALUATION-HARNESS-CONTRACT.v1.json`

Future report schema:

- `atlas.cortex.replay_evaluation_report.v1`

## Purpose

The published `70%` milestone requires a replay/evaluation harness that compares Chat/Codex outputs against Cortex outputs. The smallest honest first slice is a deterministic contract comparator over explicitly exported artifacts.

It answers:

- Did both surfaces receive the same declared case and source truth?
- Did both preserve the same scope, ownership, authority, dependency, resource, verification, and receipt constraints?
- Did either omit, contradict, or widen a required constraint?
- Are repeated evaluations byte-stable for identical inputs?
- Is the case comparable, blocked, or only partially comparable?

It does not answer which model is generally smarter or better.

## Admitted Inputs

Every input is explicit, root-relative, UTF-8, non-secret, and digest-recorded.

Required:

1. One replay case manifest using `atlas.cortex.replay_case.v1`.
2. One normalized Chat/Codex adapter artifact using `atlas.cortex.external_adapter_candidate.v1`.
3. One Cortex synthesis packet using `atlas.cortex.chat_style_synthesis_packet.v1`.
4. One Cortex execution plan using `atlas.cortex.execution_plan.v1`.
5. One frozen evaluation rubric using `atlas.cortex.replay_evaluation_rubric.v1`.

Optional:

- explicit durable source references under `docs/**`;
- prior report references for regression comparison;
- operator-provided redaction attestation;
- card or Atlas job correlation IDs.

Denied:

- hidden ChatGPT or Codex transcript access;
- private chain-of-thought or reasoning extraction;
- browser profile, account, health, payment, or personal-data scraping;
- secrets, `.env*`, tokens, cookies, or credentials;
- owner-repo files under `repos/**`;
- runtime state as authoritative input;
- live GitHub, Discord, Vercel, Supabase, or network reads;
- absolute paths or parent traversal;
- free-form artifact comparison without an admitted schema and rubric.

## Case Contract

The replay case freezes:

- `case_id`;
- objective;
- selected lane, marker, and packet;
- declared source refs and digests;
- project, component, repository, and owner;
- expected execution class;
- expected scope lock;
- expected resource claims;
- expected dependency edges;
- expected authority denials;
- expected approvals;
- expected verification, proof, commit, receipt, rollback, and recovery requirements;
- expected blocked or admissible posture;
- expected comparison fields;
- provenance and redaction attestation.

The case manifest cannot grant execution or external-action authority.

## Deterministic Comparison Model

The first harness compares normalized contract fields only. It does not use semantic embedding, model scoring, or subjective prose grading.

Comparison dimensions:

- schema compatibility;
- source digest parity;
- objective and selected-scope parity;
- project/component/repository/owner parity;
- execution-class parity;
- scope-lock parity;
- dependency-graph parity;
- resource-claim parity;
- runtime recommendation parity;
- permission-capability separation;
- external-action authority and approval parity;
- verification/proof/commit/receipt parity;
- rollback/recovery parity;
- blocker, conflict, warning, and admission posture;
- deterministic repeated-output stability.

Comparison result classes:

- `equivalent`;
- `cortex_stricter`;
- `adapter_stricter`;
- `complementary`;
- `regression`;
- `incomparable`;
- `blocked`.

`cortex_stricter` and `adapter_stricter` describe deterministic constraint-set inclusion only. They are not quality rankings.

## Report Contract

The future `atlas.cortex.replay_evaluation_report.v1` output contains:

- schema version and stable report ID;
- case ID and source digests;
- source trust classes;
- comparator and rubric versions;
- normalized adapter and Cortex projections;
- field-level comparisons;
- matched constraints;
- adapter-only and Cortex-only constraints;
- omissions and contradictions;
- authority-boundary regressions;
- dependency and collision differences;
- verification and receipt differences;
- deterministic metrics;
- prior-report regression comparison when explicitly supplied;
- result class and explanation codes;
- blockers, warnings, and skipped reasons;
- `safe_to_use`;
- next recommended packet;
- complete authority denials.

Stable identity is the digest of the contract version, case manifest, rubric, and normalized input digests.

## Failure-Closed Conditions

The harness blocks on:

- missing or invalid required schema;
- case/artifact identity mismatch;
- conflicting source digests;
- stale or unredacted input declaration;
- missing ownership;
- hidden transcript dependence;
- secret-bearing or protected paths;
- absolute paths or parent traversal;
- unknown rubric version;
- unknown comparison dimension;
- self-granted execution, final-receipt, marker, routing, deploy, Git, Discord, database, or external-mutation authority;
- nondeterministic output for identical normalized inputs;
- requested output outside explicit `tmp/atlas/**.json`.

## First Implementation Boundary

Future implementation may touch exactly:

- `ops/cortex/replay_evaluation_harness.py`
- `tests/test_cortex_replay_evaluation_harness.py`

It may read the frozen registry and existing Cortex schemas. It may write only an explicitly requested `tmp/atlas/**.json` report.

It may not change:

- existing Cortex helpers;
- `_stack`;
- Atlas Contracts;
- Playbook;
- owner repositories;
- DiscordOS;
- cards or project boards;
- marker surfaces;
- runtime state;
- secrets;
- workflows;
- live platforms.

## Required First-Implementation Proof

The first implementation must prove:

1. schema-only output is deterministic and non-authoritative;
2. equivalent normalized inputs classify `equivalent`;
3. missing adapter constraints classify `cortex_stricter` or `regression` according to the rubric;
4. missing Cortex constraints classify `adapter_stricter` or `regression` according to the rubric;
5. non-overlapping additions classify `complementary` only when the rubric admits them;
6. mismatched source digests block comparison;
7. stale, secret-bearing, hidden-transcript, absolute, traversal, owner-repo, runtime, and live-platform inputs are rejected;
8. authority widening is always a regression or blocker;
9. dependency, resource-collision, verification, receipt, rollback, and recovery differences are explicit;
10. stable repeated inputs produce byte-identical output;
11. optional prior-report comparison detects a deterministic regression;
12. no output is written without `--output`;
13. only explicit `tmp/atlas/**.json` output is admitted;
14. strict incomparable, regression, and blocker cases exit nonzero according to frozen policy;
15. no subprocess, network, model, Git, Codex, queue, scheduler, marker, card, or platform mutation path exists;
16. the final diff contains exactly the two admitted implementation files.

## Authority Boundary

- Atlas owns the case, rubric, contracts, receipts, marker, and routing truth.
- Cortex produces advisory synthesis, planning, and comparison projections.
- `_stack` remains the execution/operator plane.
- Codex remains the native execution runtime.
- DiscordOS remains the sole logical board and Discord writer.
- Human review owns any conclusion that requires subjective quality judgment.

## Marker Decision

No marker moves. `Cortex Dual-Mode Replacement Readiness` remains `60%`.

A contract freeze is not the published `70%` implementation threshold.

## Exact Next Packet

`Cortex Dual-Mode Replacement Readiness replay/evaluation harness first-implementation admission`

