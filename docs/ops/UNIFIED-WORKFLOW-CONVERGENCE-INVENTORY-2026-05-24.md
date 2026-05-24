# Unified Workflow Convergence Inventory

Date: 2026-05-24
Lane: Unified Workflow Convergence
Mode: Docs-only inventory
Status: inventory complete

## Goal

Map the current canonical workflow pieces across ATLAS root, `_stack`, Playbook, QA/LLEL proof, Fitness local and mobile work, Discord update and feedback flows, release-ledger publication, deploy authority, and manual exception handling.

This pass does not implement commands, modify Discord bot behavior, deploy, mutate Vercel or Supabase, or change product code.

## Governing Principle

ATLAS root is the coordination and reporting layer.

Owner repos remain owner truth for:

- runtime behavior
- repo-local command semantics
- product verification
- release preparation
- deploy execution details

Unified workflow convergence should connect those truths, not duplicate them.

## Current Canonical Workflow Pieces

### ATLAS root truth

ATLAS root currently owns:

- stack topology and path policy in `stack.yaml`
- stack lock truth in `stack.lock.yaml`
- root validation in `ops/validation/validate_stack.py`
- continuity and conversation coordination in:
  - `docs/ops/ATLAS-CONVERSATION-RUNBOOK.md`
  - `docs/ops/ATLAS-CONTINUITY-LANE.md`
- cross-repo program framing in:
  - `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
  - `docs/ops/PLAYBOOK-ORIGIN-RESEARCH-TRAIL-2026-05-24.md`
- lane receipts and governance checkpoints in `docs/ops/**`

ATLAS root is already the durable place where:

- receipts are packaged
- lock truth is projected
- cross-repo governance decisions are recorded
- lanes are paused or reopened intentionally

### `_stack` operator entrypoint

`_stack` currently owns the operator-facing execution layer:

- release launcher
- deploy wrappers
- deploy preflights
- shared Codex orchestration runner
- worker artifacts
- repo-entry routing for Atlas, Playbook, Lifeline, and `_stack`

Canonical `_stack` roles already visible:

- preview and production deploy authority for Fitness
- preview and production deploy wrappers for Trove and Mazer
- deploy identity fail-closed checks for Fitness, Trove, and Mazer
- shared worker and inbox orchestration for multi-repo Codex work

### Playbook governance

Playbook is still the governance-runtime owner, not ATLAS root.

Current ATLAS role relative to Playbook:

- project read-only contract status
- maintain doctrine continuity context
- route work by owner boundary
- keep root-side projections explicit

Playbook should be mandatory where the work is about:

- governance
- verify and plan doctrine
- contract extraction
- reusable workflow or repo-intelligence contracts
- mutation-scope and policy semantics

### QA/LLEL proof

Current QA and proof posture is split by owner surface:

- Fitness repo owns app verification, UI checkpoint flows, and QA/LLEL proof surfaces
- Mazer repo owns its own verify, visual, and hosted-preview proof surfaces
- `_stack` owns the operator entrypoints that run deploy-adjacent verify paths
- ATLAS root records cross-repo receipts and checkpoint posture

This is already partially converged, but still repo-specific in naming and handoff shape.

### Fitness local and mobile workflow

Fitness currently has a strong but multi-surface local workflow:

- repo-local command glossary and release-prep helpers
- repo-local QA/LLEL proof loop
- `_stack` deploy authority
- release ledger and update-draft workflow
- local versus production-data sync doctrine

This is one of the most mature current workflow families in the stack.

### Discord feedback and updates workflow

Fitness Discord workflow is explicitly split:

- feedback forum thread mutations stay inside Discord thread audit comments
- reviewed exports become planning inputs
- production deployment events create bounded update drafts
- admins publish curated user-facing updates

That means the current canonical user-facing release flow is:

1. work ships
2. production deployment is observed
3. bounded draft is created
4. human publishes curated update

### Release ledger and `#updates`

Current release narration is split across:

- repo-owned release ledger rows in Fitness
- Discord update drafts and publish commands
- root receipts and stack checkpoints

This is explicit, but not yet unified under one cross-stack operating model.

### Deploy authority

Deploy authority is now materially clearer:

- Fitness preview and prod authority: `_stack`
- Trove preview and prod authority: `_stack`
- Mazer preview and prod authority: `_stack`
- direct repo-local `vercel --prod`: exceptional or recovery-only, not default

### Manual exception handling

Manual deploy exception handling is now documented, not implicit:

- Fitness release helpers are not deploy authority
- Trove and Mazer fail closed on local Vercel identity drift
- remaining deploy risk is checkpointed, not hidden

## Workflow Map By Owner

| Workflow area | Canonical entrypoint | Owner | Receipt owner | Current state |
| --- | --- | --- | --- | --- |
| Stack governance and lane tracking | ATLAS root docs and validation | ATLAS root | ATLAS root | strong |
| Cross-repo deploy execution | `_stack` package scripts and launcher | `_stack` | `_stack` local truth + ATLAS lock repin | strong |
| Governance doctrine and contract truth | Playbook owner repo | Playbook | Playbook first, ATLAS projection second | partial projection, strong boundary |
| Fitness app verify and release prep | Fitness repo commands | Fitness | Fitness repo | strong |
| Fitness production deploy authority | `_stack` | `_stack` | `_stack` + ATLAS root | strong |
| Fitness Discord update drafting and publish | Fitness repo bot surfaces | Fitness | Fitness repo and Discord | strong but app-specific |
| Trove deploy authority | `_stack` | `_stack` | `_stack` + ATLAS root | strong |
| Mazer deploy authority | `_stack` | `_stack` | `_stack` + ATLAS root | strong |
| Conversation continuity and handoff | ATLAS root runbooks and runtime | ATLAS root | ATLAS root runtime/receipts | strong |
| Worker orchestration | `_stack` shared runner | `_stack` | `_stack` repo-local `.codex` artifacts | strong |

## Duplicate Workflow Paths

The inventory shows four important duplicate or partially-overlapping workflow families.

### 1. Verification language is split across root, `_stack`, and repo-local docs

Examples:

- root validation and lane receipts
- `_stack` deploy/verify wrappers
- repo-local verify commands and proof docs

This is legitimate in ownership terms, but operators still reconstruct the full workflow manually.

### 2. Release narrative is split across repo ledger, Discord update draft, and ATLAS receipts

Current pieces:

- Fitness release ledger row
- Fitness Discord update workflow
- root deployment and governance receipts

This is bounded, but not yet unified into one simple “release happened, here is the governed proof chain” model.

### 3. Continuity and execution are connected conceptually, but not yet one explicit operator workflow

Current pieces:

- conversation runbook
- continuity lane
- `_stack` orchestration
- Playbook convergence program

They are compatible, but not yet presented as one named end-to-end workflow model.

### 4. Deploy authority is unified in `_stack`, but supporting doctrine is still scattered

Current pieces:

- `_stack` deploy wrappers
- repo-local release-prep docs
- root deploy-exception receipts
- Vercel and Discord workflow docs

The authority is clearer than before, but the documentation still spans multiple locations.

## Missing Handoffs

### Missing handoff: repo-local release prep -> `_stack` deploy authority

Fitness is improved here, but the stack does not yet expose one cross-stack rule card or runbook that says:

- repo-local release prep ends here
- `_stack` deploy authority begins here
- root receipt packaging ends here

### Missing handoff: deploy completion -> release ledger -> Discord publish checkpoint

Fitness has the pieces, but the cross-stack operating model is still implicit:

- deploy authority is `_stack`
- release ledger is repo-owned
- public update publish is admin-curated
- ATLAS root records governance receipts

That chain needs one explicit convergence surface.

### Missing handoff: Playbook governance -> `_stack` operator execution

ATLAS already documents the owner split, but the first unified workflow map should make it explicit when:

- Playbook is mandatory
- `_stack` is mandatory
- ATLAS root is projection-only

### Missing handoff: conversation/continuity -> actionable workflow lane

Continuity is well-defined as evidence and promotion, but it is not yet fused into one operator-facing workflow map with:

- intake
- proposal
- worker execution
- deploy
- publish
- receipt

## Command Owners

### ATLAS root

Owns:

- stack validation
- stack lock truth
- lane receipts
- continuity and conversation coordination
- cross-repo convergence program docs

### `_stack`

Owns:

- deploy wrappers
- deploy preflights
- release launcher
- shared Codex runner
- worker and merge/resume orchestration

### Playbook

Owns:

- governance truth
- contract truth
- reusable workflow doctrine
- repo-intelligence and safe remediation doctrine

### Fitness

Owns:

- product verification
- release prep
- release ledger
- Discord update draft and publish implementation

### Trove and Mazer

Own:

- app/runtime verification in their own repos
- hosted-preview proof in repo-local docs

## Receipt Owners

### Root-owned receipts

Should remain in ATLAS root for:

- cross-repo governance decisions
- stack-lock repins
- convergence checkpoints
- lane inventories and pause points

### Repo-owned receipts

Should remain in owner repos for:

- product verification
- release ledger entries
- bot and deployment-app behavior
- repo-local proof surfaces

### `_stack` local truth

Should remain local to `_stack` for:

- local operator commits
- `.codex` worker artifacts
- operator-surface tests and runner state

## Discord Feedback And Update Touchpoints

Current touchpoints are concentrated in Fitness:

- feedback thread audit comments stay in Discord thread context
- reviewed exports become planning input
- production deployment creates bounded update drafts
- admin-curated publish creates the public `#updates` surface

This is currently the strongest user-visible workflow family that should inform convergence.

## Where Playbook Should Be Mandatory

Playbook should be mandatory when the question is about:

- governance rules
- verify/plan/apply doctrine
- mutation-scope enforcement
- contract and policy semantics
- reusable repo-intelligence or remediation models

ATLAS root should not duplicate those truths.

## Where `_stack` Should Be The Entrypoint

`_stack` should be the entrypoint when the work is about:

- deploy authority
- preview/prod operator actions
- release launcher execution
- shared worker dispatch
- merge/resume/orchestration behavior
- cross-repo operational command surfaces

## What Remains Manual-Only

The inventory still leaves several surfaces manual by design:

- `_stack` has no remote, so `_stack` truth commits remain local-only and require ATLAS lock acceptance
- Discord update publish is still curated/admin-driven
- remote preview/unfurl verification is still gated on an explicit deploy-backed lane
- Git auto-deploy state for Trove and Mazer is still undocumented in governed docs
- broader workflow convergence has not yet produced one operator-facing unified runbook

## Recommended First Convergence Package

The first convergence package should be small and operator-facing:

- create one stack-owned workflow handoff map that explicitly joins:
  - repo-local release prep
  - `_stack` deploy authority
  - repo-owned release ledger
  - Discord update drafting/publish boundary
  - root receipt packaging

Recommended artifact shape after this inventory:

- a short runbook or contract such as `UNIFIED-WORKFLOW-CONVERGENCE-HANDOFF-MAP`

That slice is smaller and more useful than trying to automate or rewrite everything at once.

## Recommended Next Slice

Pick one first convergence package:

- **release/deploy/update handoff map**

Reason:

- it connects the most mature existing workflow pieces
- it reduces operator reconstruction cost
- it does not require bot changes, deploy changes, or Playbook contract mutation
- it creates a reusable template for later convergence work

## No-Change Confirmation

This pass did not:

- implement new commands
- change Discord bot behavior
- deploy anything
- mutate Vercel
- mutate Supabase
- touch Fitness product code
