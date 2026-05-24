# Unified Playbook / Core Pattern Extraction Handoff

Date: 2026-05-24
Lane: Unified Workflow Convergence
Mode: docs-only doctrine map
Status: extraction handoff baseline recorded

## Goal

Define how rules, patterns, failure modes, receipts, and reusable workflow candidates move from stack lanes into ATLAS root doctrine, Playbook governance surfaces, Cortex-readable planning context, and future automation-candidate queues.

This pass does not migrate Cortex runtime ownership, implement Playbook features, add bot commands, or automate doctrine promotion.

## Governing Split

- ATLAS root records stack-visible doctrine, convergence state, lock consequence, and cross-repo receipts.
- Playbook owns reusable governance doctrine, verify and plan semantics, workflow contracts, and promoted rule or pattern truth.
- Cortex may consume planning context and doctrine summaries without becoming runtime owner.
- Owner repos keep repo-local proof, runtime behavior, and product-specific evidence.
- `_stack` owns shared operator execution and deploy authority, not doctrine truth by default.

## Admission Rule

Nothing becomes stack-readable doctrine just because it was said once in chat.

Required promotion chain:

1. lane work happens in the owner surface
2. receipt-worthy proof is produced
3. ATLAS records the cross-repo or program consequence
4. reusable rule, pattern, failure mode, or command candidate is extracted
5. Playbook-facing doctrine is promoted only after evidence and wording are stable

Failure mode:

- chat-only insight masquerades as doctrine even though it has no receipt, no owner boundary, and no repeatability proof

## What Counts As A Rule

A Rule is a bounded normative statement that constrains operator or system behavior.

A candidate statement counts as a Rule only when it:

- can be stated as "must", "must not", or equivalent bounded requirement
- protects trust, ownership, proof, or safety posture
- applies across more than one isolated local change
- is supported by one or more receipts, decisions, or repeat failures

Examples already visible in the stack:

- no `tmp` source-truth fallback
- no manual deploy by default
- no Discord post before proof
- repo-local release prep does not imply deploy authority
- declared mutation scope must be enforced before apply succeeds

## What Counts As A Pattern

A Pattern is a reusable workflow or structural sequence that keeps recurring across lanes.

A candidate statement counts as a Pattern when it:

- describes an ordered shape rather than a one-off rule
- appears across multiple repos, lanes, or operator actions
- helps people reproduce a stable outcome
- stays useful even when the surrounding product surface changes

Examples:

- intent -> command owner -> proof -> release or update -> receipt -> doctrine
- verify -> plan -> apply -> verify
- repo-local prep -> `_stack` deploy authority -> release ledger -> Discord update -> ATLAS receipt
- repeated request -> automation candidate -> owner and risk classification -> command contract

## What Counts As A Failure Mode

A Failure Mode is a named recurrent way the stack can drift, confuse operators, or bypass governance.

A candidate statement counts as a Failure Mode when it:

- has already happened or is strongly evidenced by receipts
- can be recognized again in future work
- explains how a workflow becomes unsafe, noisy, or misleading
- points back to a rule or pattern that prevents it

Examples:

- wrong repo or wrong branch deploy authority confusion
- advisory scope bundles mistaken for safety
- Discord publication before proof
- correct-but-dense truth reducing adoption
- repeated mechanical work staying in chat forever instead of becoming a command

## What Counts As A Reusable Command Candidate

A reusable command candidate is not doctrine alone. It is a repeated bounded workflow that looks stable enough to graduate into `_stack`, Playbook, or bot-owned operator surfaces later.

A candidate qualifies when it:

- repeats often enough to justify command cost
- has a clear owner boundary
- has explicit verification
- has an explicit rollback or safe failure posture
- does not depend on hidden personal knowledge

Examples already emerging:

- release proof summary before Discord publication
- stack-side doctrine extraction checklist after lane closeout
- repeated updates-channel publishing with correct type, title, and embed defaults
- repeated validation and lock-decision packaging at root

Non-example:

- a one-time chat observation with no stable proof surface

## Where ATLAS Records Stack-Level Doctrine

ATLAS root should record stack-readable doctrine when the result affects:

- more than one repo
- convergence posture
- lock truth
- owner-boundary clarification
- strategic program direction

Canonical ATLAS doctrine and projection surfaces:

- `docs/PLAYBOOK_NOTES.md`
- `docs/ops/UNIFIED-*.md`
- `docs/ops/*CHECKPOINT*.md`
- `docs/ops/*DECISION*.md`
- `docs/ops/*INVENTORY*.md`
- `docs/ops/PLAYBOOK-ORIGIN-RESEARCH-TRAIL-2026-05-24.md`

ATLAS should record:

- stack-facing summaries
- convergence handoff maps
- pause or reopen checkpoints
- marker movement justification
- receipt linkage to reusable doctrine

ATLAS should not become:

- the runtime owner of Playbook contracts
- a duplicate repo-local proof ledger
- a noisy dump of every local lesson before it is shaped

## Where Playbook Records Reusable Governance

Playbook should hold reusable governance when the extracted lesson becomes:

- verify or plan doctrine
- mutation-scope semantics
- contract or admission logic
- reusable remediation workflow
- generalized repo-intelligence pattern

Playbook-facing doctrine should receive:

- promoted Rules
- promoted Patterns
- promoted Failure Modes
- workflow contracts that should apply outside the original lane

Promotion threshold:

- at least one linked receipt or checkpoint
- clear wording
- owner boundary preserved
- evidence that the lesson is reusable, not merely local

## Where Cortex Can Consume Planning Context

Cortex may read and use planning context from:

- ATLAS convergence maps
- Playbook doctrine summaries
- root receipts and checkpoints
- reviewed exports and lane inventories

Cortex may consume this as:

- planning context
- prioritization context
- admission or triage context
- structured handoff input

Cortex should not, from this lane:

- become runtime owner
- mutate doctrine automatically
- replace Playbook promotion gates
- bypass owner repos or `_stack`

Pattern:

- ATLAS projection -> Cortex-readable planning context -> human or governed promotion path

## How Discord Feedback And Update Lessons Become Doctrine

Discord-facing lessons become doctrine only after they pass through bounded workflow surfaces:

1. feedback card or update workflow happens in Fitness Discord OS
2. thread audit comments, reviewed exports, update drafts, or publish receipts capture evidence
3. ATLAS records the cross-stack consequence if the lesson affects convergence or workflow policy
4. Playbook notes receive the reusable rule, pattern, or failure mode

Valid doctrine candidates from Discord work:

- card mutation versus public update separation
- no Discord post before proof
- public versus operator channel boundaries
- release-ledger dependency for public publication
- feedback closeout requirements

Invalid shortcut:

- promote forum chatter or one operator complaint directly into doctrine with no bounded evidence

## How QA/LLEL Failures Become Durable Patterns

QA/LLEL failures should become doctrine only after they are classified.

Required chain:

1. QA or local proof fails
2. owner repo or root proof lane records the failure
3. the failure is classified as local defect, workflow gap, false signal, or governance gap
4. ATLAS records the stack consequence if cross-repo behavior is affected
5. Playbook notes promote the reusable prevention pattern

Good doctrine examples:

- repo blockers exposed by QA belong to the owning repo
- warning budgets need governance before they become promotion gates
- local proof and release proof are different evidence classes

## How Repeated Operator Asks Become AI Repetition-to-Automation Candidates

Repeated operator asks should not all become doctrine. Some should become automation candidates instead.

Promotion split:

- if the lasting value is a reusable behavioral truth, promote doctrine
- if the lasting value is mechanical repetition with clear boundaries, create an automation candidate

Candidate flow:

1. repeated ask appears across chats or lanes
2. receipt or checkpoint notes the repetition
3. owner and risk are classified
4. command candidate is recorded
5. later implementation lane decides whether it belongs in `_stack`, Playbook, or Discord OS

Examples:

- updates-channel posting format checks
- release-to-receipt closeout packaging
- doctrine extraction checklists
- repeated validation summaries

## Required Receipt Links Before Doctrine Is Admitted

Doctrine admission should link back to bounded evidence.

Minimum evidence set:

- one receipt, decision, or checkpoint that proves the lesson mattered
- one owner surface where the behavior occurred
- one sentence explaining why the lesson is reusable

Stronger evidence set:

- multiple receipts across lanes
- proof that the same pattern or failure recurred
- proof that a preventive rule improved later work

Receipt classes that qualify:

- ATLAS root decision receipts
- convergence maps
- lock decisions
- repo-local release or proof receipts
- reviewed Discord update or feedback workflow receipts

## Doctrine Handoff By Lane

| Source lane | Primary evidence owner | ATLAS root role | Playbook role | Cortex role | Automation-candidate outcome |
| --- | --- | --- | --- | --- | --- |
| Deploy and release | `_stack` and owner repo | record lock and governance consequence | promote deploy-authority rules and failure modes | read planning consequences | `_stack` preflight and closeout helpers |
| QA/LLEL and proof | owner repo and root proof receipts | package stack-visible checkpoint | promote proof and verification patterns | consume readiness context | proof summary or gating helpers |
| Discord feedback and updates | Fitness repo | record workflow consequence and convergence impact | promote publication and feedback-boundary doctrine | consume user-signal and workflow context | bot or checklist candidates |
| Brand and preview verification | ATLAS plus owner repo | record source-truth and verification posture | promote cache, proof, and source-truth rules | consume verification planning context | verification report helpers |
| Manual deploy burn-down | `_stack`, owner repos, ATLAS receipts | record checkpoint and residual gaps | promote fail-closed deploy doctrine | consume risk and sequencing context | deploy-authority checks |
| Repeated operator asks | ATLAS continuity and receipts | classify repetition lane state | promote only the reusable behavioral truths | consume future command candidates | `_stack` or Playbook command candidates |

## Non-Goals

This package does not:

- migrate Cortex into runtime ownership
- implement Playbook features
- add bot commands
- automate doctrine promotion
- replace repo-local release ledgers
- replace `_stack` operator execution surfaces

## Interpretation

The canonical extraction answer is now:

- owner repos generate runtime proof and local evidence
- `_stack` generates shared operator evidence where execution is shared
- ATLAS records stack-visible consequence, convergence state, and doctrine linkage
- Playbook receives the reusable governance truth after evidence is stable
- Cortex reads planning context without owning runtime
- repeated asks that are mostly mechanical should become automation candidates, not endless chat work

## Marker Interpretation

This package justifies:

- Unified Workflow Convergence: `60%`
- Core Pattern Convergence: `10%`
- Playbook Everywhere + Cortex Interface: `10%`
- Knowledge Capture & Transfer: `20%`
- AI Repetition-to-Automation Pipeline: `10%`

It does not yet justify:

- Cortex runtime migration
- Playbook feature implementation
- bot or `_stack` automation implementation
