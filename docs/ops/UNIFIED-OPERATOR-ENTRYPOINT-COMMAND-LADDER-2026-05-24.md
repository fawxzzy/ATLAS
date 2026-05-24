# Unified Operator Entrypoint & Command Ladder

Date: 2026-05-24
Lane: Unified Workflow Convergence
Mode: docs-only operating map
Status: operator ladder baseline recorded

## Goal

Define the canonical operator flow across `_stack`, Playbook, QA/LLEL, Discord OS, repo-local scripts, and ATLAS root receipts so operator intent resolves into one governed ladder instead of several disconnected local habits.

This pass does not deploy, post to Discord, mutate Vercel, mutate Supabase, change repo implementation behavior, or introduce new command surfaces.

## Governing Rules

- Start from the owner surface that matches the work type instead of improvising a root-side shortcut.
- Repo-local commands may prepare, verify, build, and prove; they do not become deploy authority by implication.
- `_stack` owns governed preview and production deploy authority for Fitness, Trove, and Mazer.
- Playbook owns governance doctrine, contract semantics, reusable verify and plan logic, and promoted workflow knowledge.
- Discord consumes proof; it does not create deploy or engineering truth.
- ATLAS root records cross-repo consequence, lane state, lock truth, and continuity receipts.
- `tmp` is never a source-of-truth fallback.
- No Discord post before proof.
- No manual deploy by default.

## Canonical Starting Point By Work Type

| Work type | Canonical starting point | Primary owner | First proof gate | Downstream handoff |
| --- | --- | --- | --- | --- |
| Product change | owner repo local branch and repo-local verify path | owner repo | repo-local verify/build or app-specific proof | QA/LLEL or release-readiness boundary |
| Docs change | owner repo docs or ATLAS root docs depending on truth owner | owner repo or ATLAS root | path/policy consistency and repo-local verify if repo-owned | receipt packaging if cross-repo consequence exists |
| Release or deploy | repo-local release prep, then `_stack` deploy wrapper | owner repo, then `_stack` | repo-local readiness, then `_stack` preflight | release ledger, publish boundary, ATLAS receipt if needed |
| QA or proof | repo-local QA/LLEL or local server workflow | owner repo | deterministic QA/LLEL or live local route proof | release-readiness or feedback closeout |
| Discord update | repo-owned update draft or publish surface | owner repo Discord OS | shipped proof and release-ledger evidence | public `#updates` post, then ATLAS receipt if stack consequence matters |
| Incident or recovery | `_stack` recovery runbook or owner-repo recovery surface | `_stack` or owner repo | bounded incident classification and recovery proof | recovery receipt and doctrine extraction |
| Brand or preview verification | ATLAS planning receipt, then owner repo local proof or `_stack` deploy-backed proof lane | ATLAS root plus owner repo | source hash and consumer hash proof, then live-surface proof | remote verification plan or closeout receipt |
| Automation or batch job | `_stack` operator surface or Playbook planning lane | `_stack` or Playbook | bounded contract, owner clarity, and verification plan | automation receipt, then later implementation lane |

## Canonical Ladder

1. Classify the work type and choose the owner surface.
2. Run repo-local preparation or proof where the owner repo owns the behavior.
3. Escalate into `_stack` only when the task becomes shared execution, deploy, operator orchestration, or multi-repo flow.
4. Escalate into Playbook when the task becomes governance, contract, reusable doctrine, or repeatable pattern extraction.
5. Publish to Discord only after proof and release evidence already exist.
6. Package cross-repo consequence and lane state in ATLAS root.
7. Extract reusable rules, patterns, and failure modes into Playbook-facing doctrine after the workflow completes.

## Command Ownership

## `_stack`

`_stack` owns the operator entrypoint when the task becomes shared execution or deploy authority.

Canonical `_stack` surfaces already in use:

- `pnpm run fitness:deploy:preflight`
- `pnpm run fitness:deploy:preview`
- `pnpm run fitness:deploy:prod`
- `pnpm run trove:deploy:preflight`
- `pnpm run trove:deploy:preview`
- `pnpm run trove:deploy:prod`
- `pnpm run mazer:deploy:preflight`
- `pnpm run mazer:deploy:preview`
- `pnpm run mazer:deploy:prod`
- `pnpm run codex:stack:verify`
- `pnpm run codex:atlas:task`
- `pnpm run codex:playbook:task`
- `pnpm run codex:lifeline:task`

`_stack` should be the entrypoint for:

- governed deploys
- deploy preflights
- shared Codex runner tasks
- operator-surface verification
- shared release-launcher surfaces

`_stack` should not become:

- the place where product truth is authored
- the place where feedback cards are reviewed as engineering truth
- a replacement for repo-local verify and QA commands

## Playbook

Playbook owns:

- verify and plan doctrine
- contract semantics
- repo-intelligence and governance framing
- reusable workflow doctrine
- promoted rules, patterns, and failure modes

Playbook should be mandatory when the task is about:

- governance contracts
- mutation-scope semantics
- reusable verify and plan logic
- doctrine extraction from repeated evidence
- turning repeated operator behavior into a governed contract candidate

Playbook should not be treated as:

- the live Vercel deploy wrapper
- the release ledger
- the Discord publication surface

## Repo-Local Scripts

Owner repos own:

- product verify and build semantics
- local dev and proof loops
- release preparation
- product-specific QA/LLEL
- repo-owned ledgers and update-draft workflows

Examples already in use:

### Fitness

- `npm run verify`
- `npm run typecheck`
- `npm run build`
- `npm run release:fitness:prepare`
- `npm run release:fitness:record`
- `npm run release:fitness:ready`
- `npm run qa:fitness:ui-checkpoint`
- `npm run verify:mobile-regression`
- `npm run feedback:board:export`
- `npm run doctor:discord-community`

### Trove

- `npm run verify`

### Mazer

- `npm run verify`
- `npm run build`
- `npm run test`

Repo-local scripts may:

- verify
- build
- prepare
- record repo-owned evidence
- export reviewed inputs

Repo-local scripts may not:

- imply deploy authority when `_stack` owns deploy
- replace root receipts for cross-repo consequence
- replace Playbook governance doctrine

## Discord Bot / Discord OS

Discord OS owns:

- feedback intake
- bounded thread and card mutations
- update drafts and curated publish commands
- public versus private channel boundaries

Discord command or panel surfaces are valid for:

- user feedback intake
- admin review of update drafts
- controlled publication after proof

Discord is not valid for:

- deploy authorization
- ATLAS truth mutation
- skipping review or proof gates

## ATLAS Root Receipts

ATLAS root owns:

- lane inventories
- convergence maps
- stack-lock truth and repins
- cross-repo checkpoints
- continuity and pause or resume state
- root validation receipts

ATLAS root should capture:

- what crossed repo boundaries
- what changed stack truth
- what should be paused or reopened later
- what doctrine needs to remain visible at the coordination layer

ATLAS root should not duplicate:

- repo-owned release ledgers
- repo-owned bot runtime state
- repo-local product verification as if root owns it

## Escalation Ladder

### 1. Plan

Choose the owner surface first.

- product or repo behavior: owner repo
- governed deploy or shared execution: `_stack`
- doctrine, contract, or reusable workflow semantics: Playbook
- cross-repo continuity and lane packaging: ATLAS root

### 2. Implement

Implement inside the owner repo or `_stack` only when the task belongs there.

Do not widen into unrelated repos from root.

### 3. Verify

The owning repo proves local behavior first.

Examples:

- Fitness local proof and QA/LLEL
- Trove `npm run verify`
- Mazer `npm run verify`
- `_stack` operator-surface proof with `pnpm run codex:stack:verify`

### 4. Release

When the work becomes ship intent:

- repo-local release prep ends
- `_stack` deploy authority begins
- fail-closed preflights must pass before Vercel is reachable

### 5. Publish Update

Public Discord updates are downstream of:

- proof
- shipped or release evidence
- curated user-facing copy

No publish before proof.

### 6. Capture Doctrine

Once a workflow produces stable repeated behavior:

- ATLAS records the stack consequence
- Playbook captures reusable rules, patterns, and failure modes

### 7. Close Receipt

ATLAS root closes the lane slice with:

- receipt
- validation result
- lock decision if a repo head moved
- explicit pause or next move

## Forbidden Shortcuts

- no `tmp` source truth
- no manual deploy by default
- no Discord post before proof
- no repo-local deploy authority when `_stack` owns deploy
- no root-side product edits across unrelated repos
- no branching without a named owner repo or worktree boundary
- no feedback-thread churn treated as release proof
- no release-prep command treated as if it were deploy authorization

## Automation Candidates

This map exposes several repeated steps that are stable enough to classify, but not yet fully automated.

### `_stack` candidates

- one command that prints the correct operator starting point by work type
- a shared preflight summary surface that reports repo readiness plus deploy-authority status
- a release-to-receipt helper that points from deploy completion to ledger, update, and ATLAS packaging

### Playbook candidates

- a repeated doctrine extraction checklist for workflow receipts
- a reusable command-ladder contract that can classify whether a task belongs to repo-local, `_stack`, Playbook, Discord OS, or ATLAS root

### Discord workflow candidates

- a publish-readiness helper that proves release ledger plus deploy proof exists before update publish
- a feedback closeout to release-promotion checklist that keeps thread audit history and public update format separate

### Validation and reporting candidates

- a root-side report that summarizes:
  - repo-local proof complete
  - `_stack` deploy authority status
  - release ledger recorded
  - Discord update published or intentionally deferred
  - ATLAS receipt packaged

Rule:

- repetition should graduate into governed command surfaces only after the owner boundary, proof requirement, and rollback path are explicit

## Open Gaps

- `_stack` still has no remote, so `_stack` operator-truth commits remain local-only and require ATLAS lock acceptance.
- Discord publication automation is not fully unified with release ledger and ATLAS receipt closeout.
- Playbook Everywhere + Cortex Interface is still inactive as a live operator layer.
- AI Repetition-to-Automation Pipeline is still early and mostly planning-only.
- Git auto-deploy state for Trove and Mazer is still not documented in governed surfaces.
- There is still no single operator-facing command that answers the ladder automatically; this map is the contract that should drive that later surface.

## Operator Interpretation

The canonical operator answer is now:

- start in the owner repo for product truth, local proof, and release preparation
- start in `_stack` for governed deploys and shared operator execution
- start in Playbook for governance, contracts, and reusable workflow doctrine
- start in Discord OS for community intake and curated downstream publication only
- finish in ATLAS root when cross-repo consequence, lane state, or lock truth must be recorded

If the work does not fit one of those starts cleanly, the right action is to classify it first, not to improvise a shortcut.

## Marker Interpretation

This package justifies:

- Unified Workflow Convergence: `50%`
- AI Repetition-to-Automation Pipeline: `5%`

It does not yet justify movement in:

- Playbook Everywhere + Cortex Interface
- Discord Workflow, Publication & Docs Reliability

Those lanes need live command adoption and publish-path reliability proof, not just a better map.
