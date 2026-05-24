# AI Long-Run Batch Orchestration

Date: 2026-05-22
Status: Active lane
Progress: `20%`

## Purpose

This lane turns the existing long-run AI batching research into explicit ATLAS doctrine before any unattended multi-hour execution model is normalized into stack operations.

This is a doctrine and contract lane first, not an implementation sprint.

Adjacent but distinct lane:

- `AI Repetition-to-Automation Pipeline`
  - detects repeated AI, Codex, and operator asks
  - converts safe repetitive workflows into governed command surfaces
  - is not the same problem as long-run batch execution
- `Core Pattern Convergence`
  - tracks whether the strongest reusable ideas from one lane actually spread into the rest of the stack
  - is not the same problem as either batch execution or command-surface automation

## Current Read

- research and design direction exist
- the clean operating shape is visible
- the lane is not yet integrated into `_stack`, Playbook, ATLAS lane manifests, or a single supervised pilot
- no current root doctrine should imply that one giant interactive Codex session is the approved batching model
- this lane is part of the convergence program, not a separate side project
- this lane should not absorb the separate repetition-to-automation problem, because repeated short tasks and long supervised jobs have different contracts and risks

## Governing Rule

Long-run AI batching is a job-oriented supervised workflow, not one indefinite interactive root session.

## Target Model

The approved future direction is:

- job-oriented local supervisor
- bounded jobs
- isolated worktrees
- durable checkpoints
- explicit verification gates
- human-readable lane and job manifests

## Ownership Split

ATLAS root owns:

- stack doctrine
- lane definitions
- path and boundary rules
- cross-repo planning
- pilot selection criteria

`_stack` owns:

- execution-oriented orchestration contracts
- worker flow
- resume and merge behavior
- supervised job dispatch semantics

Playbook owns:

- reusable workflow doctrine
- verification expectations
- completion and closeout discipline

Owner repos own:

- repo-local truth
- repo-local verification
- repo-local implementation changes

## Required Lane Contracts

Before long unattended batching is allowed, each lane or job should declare:

- owner repo
- target branch or worktree
- allowed write scope
- checkpoint surface
- verification gate
- closeout artifact
- park or escalation rule

## Sequencing

1. Turn the research into ATLAS doctrine.
2. Define lane, job, and worktree contracts.
3. Decide what belongs to `_stack` versus Playbook versus ATLAS root.
4. Build one supervised single-lane pilot.
5. Only then allow multi-hour or multi-lane unattended batches.

## First Pilot Shape

The first pilot should be intentionally narrow:

- one owner repo
- one isolated worktree
- one bounded objective
- one explicit checkpoint path
- one required verification gate
- one human review closeout

Anything larger should wait until the single-lane pilot proves the contracts are real.

## Non-Goals

- do not normalize giant unattended root sessions as the default operator model
- do not let long-run batching bypass repo ownership
- do not let long-run batching bypass verification gates
- do not create a second orchestration truth store at root
- do not enable multi-lane unattended batching before the single-lane pilot is stable

## Failure Modes

- branch contamination from undeclared execution surfaces
- mixed-repo work inside one long-running session
- unbounded partial progress with no checkpoint contract
- hours of output with no clear verification boundary
- repo truth drifting because orchestration, doctrine, and implementation ownership are blurred

## Immediate Next Work

- keep this lane as doctrine only
- project the lane into stack planning and marker tables
- define the lane or job contract shape
- route future execution semantics into `_stack`
- route future reusable closeout and verification semantics into Playbook
- choose one supervised pilot only after Branch & Worktree Normalization is further along

## Current Sequencing Constraint

This lane remains doctrine and planning only until root normalization is further along.

- do not implement unattended multi-hour execution while Branch & Worktree Normalization is still active
- do not use current lock drift or preserved root residue as the baseline for batch orchestration contracts
- do the doctrine, lane-contract, and ownership split work first; implementation belongs later through `_stack` and Playbook

## Convergence Placement

This lane currently sits in the program as:

1. Canonical Repo Restoration
2. Tmp Dependency Elimination
3. Duplicate Surface Decommission
4. Branch & Worktree Normalization
5. Brand Asset Canonicalization
6. Preview Cache & Surface Consistency
7. Operator Secret Path Hygiene
8. Manual Deploy Exception Burn-Down
9. Discord Workflow, Publication & Docs Reliability
10. Unified Workflow Convergence
11. Playbook Everywhere + Cortex Interface
12. Truth Map & ATLAS Book
13. Full Stack Re-sync, Clean & Closeout
14. Post-Convergence Lane Split Readiness

This AI lane remains cross-cutting doctrine rather than a reason to skip the earlier canonical repo and `tmp/` restoration work.

## Distinction From Repetition Automation

This lane answers:

- how do we run bounded long jobs safely
- how do we checkpoint and verify multi-hour execution

The separate `AI Repetition-to-Automation Pipeline` lane answers:

- which repeated asks should stop consuming fresh AI context
- which workflows should become `_stack`, Playbook, or bot commands
- what verification, receipt, and rollback rules those commands need

## Dependency On Branch Discipline

This lane depends on explicit branch and worktree discipline.

Long-run batching should not start until:

- the owner repo is explicit
- the target branch or worktree is explicit
- the write scope is explicit
- the checkpoint and verification contract are explicit

## Marker Table

- Verta Absorption: `99%`
- Archive Normalization: `100%`
- ATLAS Core Phase: `92%`
- `_stack` Readiness: `40%`
- Foundation Alignment: `100%`
- Lifeline Readiness: `97%`
- Playbook Maturity: `92%`
- Cortex Readiness: `35%`
- Fitness Source-of-Truth Reset: `100%`
- Fitness QA/LLEL Workflow: `96%`
- Fitness Branch Cleanup / Main-Only Governance: `96%`
- Fitness Recovery Preservation: `80%`
- Canonical Repo Restoration: `0%`
- Tmp Dependency Elimination: `0%`
- Duplicate Surface Decommission: `0%`
- Branch & Worktree Normalization: `92%`
- Brand Asset Canonicalization: `0%`
- Preview Cache & Surface Consistency: `0%`
- Operator Secret Path Hygiene: `0%`
- Manual Deploy Exception Burn-Down: `0%`
- Unified Workflow Convergence: `0%`
- Inventory & Truth Map: `15%`
- Full Stack Re-sync, Clean & Closeout: `22% paused`
- Vision & Future Alignment: `0%`
- Dependency Untangling: `0%`
- Core Pattern Convergence: `0%`
- Playbook Everywhere + Cortex Interface: `0%`
- Knowledge Capture & Transfer: `10%`
- Feedback Loop Readiness: `0%`
- Sandbox Simulation Readiness: `0%`
- AI Long-Run Batch Orchestration: `20%`
- AI Repetition-to-Automation Pipeline: `0%`
- Truth Map & ATLAS Book: `0%`
- Discord OS Extraction Review: `0%`
- Discord Workflow, Publication & Docs Reliability: `0%`
- Post-Convergence Lane Split Readiness: `0%`
