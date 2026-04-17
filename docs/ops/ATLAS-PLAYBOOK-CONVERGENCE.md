# ATLAS Playbook Convergence And Continuity

This document is the stack-owned roadmap for making Playbook alignment and conversation continuity explicit, queryable, and verifiable across the ATLAS stack.

It is a coordination artifact for the ATLAS stack root, not a license to duplicate repo-owned truth into the root.

## Grounding

This roadmap is grounded in current stack doctrine and preserved artifacts:

- `README-STACK.md` defines the root as a coordination layer, not an umbrella monorepo.
- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md` keeps Playbook as the repo-local governance owner.
- `docs/architecture/CODEX-HANDOFF-CONTRACT.md` already defines a structured handoff lane under `runtime/receipts/handoffs/`.
- `docs/architecture/ATLAS-RETENTION-AND-MEMORY-POLICY.md` explicitly rejects chat transcript state as canonical memory.
- `docs/ops/ATLAS-CONVERSATION-RUNBOOK.md` already preserves grounded turn artifacts without treating raw transcript as durable truth.
- `docs/architecture/PLAYBOOK-INGEST-PIPELINE.md` and `docs/knowledge/IMPORT-RUNBOOK.md` already define import, evaluation, normalization, catalog, and promotion lanes.
- `docs/memory/plans/wave-9-operator-productization-and-debt-burndown.json` captures the current operator-cockpit wave and remains active.
- `docs/ops/ATLAS-CONTINUITY-LANE.md` defines the stack-owned continuity lane and promotion routing on top of the existing handoff and memory surfaces.
- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md` grounds the next PR slices against the repos and git remotes actually visible in this workspace.

## Program Intent

ATLAS is already operating in a Playbook-compatible way in several places, but current root truth does not prove that every in-scope repo has explicitly adopted the same contract or that drift is measurable.

This program closes that gap through two tracks:

- Track A: Playbook convergence across repos
- Track B: durable context continuity across Codex and ChatGPT work

## Current Root Consumption

The current root tranche consumes the landed Playbook owner export read-only from:

- `repos/fawxzzy-playbook/exports/playbook.contract.example.v1.json`
- `repos/fawxzzy-playbook/exports/playbook.contract.schema.v1.json`
- `repos/fawxzzy-playbook/docs/contracts/PLAYBOOK-CONTRACT.md`

The root-side read models that project this owner truth are:

- `ops/atlas/playbook_contract.py`
- `ops/atlas/continuity.py`
- awareness slices:
  - `playbook_contract_status`
  - `playbook_adoption_summary`
  - `playbook_repo_adoption`
  - `playbook_drift`
  - `continuity_coverage`
  - `continuity_source_inventory`
  - `continuity_promotion_queue`
  - `continuity_source_groups`
  - `continuity_search_status`

Supporting stack-owned schemas now live at:

- `schemas/atlas.playbook.adoption.report.v1.json`
- `schemas/atlas.continuity.source.manifest.v1.json`

These surfaces are projections only. They do not create a second canonical store for Playbook doctrine.

## Non-Goals

- do not merge child repos into the stack root
- do not vendor Playbook internals into ATLAS root
- do not treat raw transcript piles as canonical memory
- do not reopen voice as the primary maturity gate for this program
- do not make opportunistic edits across unrelated repos from a root session

## Continuity Model

The continuity lane is three-layer by design:

1. Raw traceability artifacts remain imports or runtime evidence, not doctrine.
2. Every meaningful Codex or ChatGPT work session should yield a structured handoff artifact.
3. Stable outcomes are promoted into initiatives, plans, decisions, knowledge, and receipts.

Current path mapping uses existing stack lanes:

- raw imported archives and exported chat material -> `data/imports/knowledge/**`
- structured session handoffs -> `runtime/receipts/handoffs/**`
- promoted durable memory -> `docs/memory/**`
- promoted durable knowledge -> `docs/knowledge/**`
- normalized query surfaces -> `runtime/cortex/catalog/**`

No new canonical path class is introduced by this roadmap.

## Gates

| Gate | Objective | Exit Criteria | Primary Outputs |
| --- | --- | --- | --- |
| `G0 posture-lock` | Turn the reconstructed strategy into explicit stack doctrine without breaking the root boundary. | Scope, non-goals, evidence refs, and an initial adoption matrix exist in root-owned docs. | `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`, `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`, related plan and initiative memory artifacts |
| `G1 contract-extraction` | Export the canonical Playbook principles, patterns, and verification expectations into explicit contracts. | Playbook publishes one human-readable spec and one machine-readable contract that root tooling can reference by version. | Playbook repo spec, Playbook contract artifact, root references to the contract |
| `G2 continuity-lane` | Make preserved conversations and handoffs queryable without promoting transcript residue into doctrine. | Structured handoffs are required for serious sessions, prior archives have an import path, and promotion from handoff or archive into memory/knowledge is documented and testable. | `schemas/atlas.continuity.handoff.v1.json`, continuity runbook updates, continuity promotion flow, import/query references |
| `G3 core-repo-rollout` | Align the stack control surfaces and the core operator repos to the Playbook contract. | `stack`, `atlas`, `playbook`, `lifeline`, and `_stack` each have an explicit adoption state, a repo-local slice, and a verification surface. | repo-local PRs, updated verify hooks or docs, adoption receipts |
| `G4 application-rollout-and-reporting` | Extend adoption status into the application repos and publish drift as a stack-visible report. | Every in-scope application repo is marked `adopted`, `verified`, `partial`, `missing`, or `n/a` with an evidence ref, and stack reporting exposes both convergence and continuity health. | application repo PRs, stack report surface, validation or cockpit summary |

## Phase Plan

### Phase 1: Posture Lock

Acceptance criteria:

- the root doctrine says this is a convergence program, not a root merge
- the adoption matrix is evidence-based and explicitly provisional until repo-local verification lands
- operator-cockpit work remains active rather than being silently replaced

Primary slices:

- stack root PR: publish this roadmap and the adoption matrix
- stack root PR: add structured memory artifacts so the program is queryable by initiatives and plans

### Phase 2: Contract Extraction

Acceptance criteria:

- Playbook principles and pattern checks are addressable outside prose
- root context-pack routing can pull contract refs by intent
- repo-local verify flows can report which contract version they target

Primary slices:

- Playbook repo PR: export the canonical principles, patterns, and checklist contract
- stack root PR: point intent routing and roadmap docs at the new contract artifact

### Phase 3: Continuity Lane

Acceptance criteria:

- serious sessions produce a structured handoff instead of relying on transcript scraping
- imported chat or archive material is cataloged as traceability evidence, not mistaken for doctrine
- promotion from handoff or archive into initiative, memory, knowledge, and receipt lanes is documented and repeatable

Primary slices:

- stack root PR: standardize a structured conversation-handoff authoring flow on top of the existing handoff contract
- stack root PR: validate serious handoffs against `schemas/atlas.continuity.handoff.v1.json`
- stack root PR: document promotion from handoff or imported archive into memory and knowledge lanes
- Atlas repo PR: update context-pack selection or query surfaces so handoff and contract refs are retrievable by intent

### Phase 4: Core Repo Rollout

Acceptance criteria:

- `playbook`, `lifeline`, and `_stack` each have explicit repo-local adoption work tied to the shared contract
- `stack` and `atlas` expose root-side visibility and context routing for the same contract
- the matrix status for each core surface is backed by a repo-local or stack-owned verification artifact

Primary slices:

- Lifeline repo PR: align approvals, receipts, and execution surfaces to the shared contract
- `_stack` repo PR: align merge, resume, and orchestration patterns to the shared contract
- Atlas repo PR: align context-pack and operator-facing retrieval to the shared contract
- stack root PR: add verification or reporting that consumes the adoption matrix

### Phase 5: Application Rollout And Reporting

Acceptance criteria:

- each in-scope application repo has an explicit adoption decision instead of silent drift
- landed repo-local adoption work is projected honestly at root
- `verified` remains blocked until the stack has an explicit, evidence-backed promotion gate
- the stack can report both convergence status and conversation-continuity health from saved artifacts
- repo-local rollout remains scoped to the owning repo

Primary slices:

- application repo PRs: add repo-local adoption or document `n/a` where justified
- stack root PR: project landed repo-local adoption evidence read-only into awareness and cockpit
- stack root PR: add the explicit adopted-to-verified gate and root-visible verification report

## First Repo-Local PR Slices

| Surface | First Slice | Done When |
| --- | --- | --- |
| `playbook` | Export canonical Playbook principles and checks as a human spec plus machine-readable contract. | Root docs and repo-local verify can reference one contract version and one contract path. |
| `lifeline` | Align approval, receipt, and execution surfaces to the shared contract. | Lifeline docs or verify output can show which Playbook contract version is implemented. |
| `_stack` | Align worker merge, resume, and orchestration patterns to the shared contract. | Resume and merge flows cite the contract and verification is explicit. |
| `atlas` | Pull contract refs and continuity refs by intent instead of broad context dumps. | Context or awareness surfaces can retrieve the right contract and continuity artifacts deterministically. |
| `fitness` | Repo-local adoption slice is landed. | Matrix status is explicit at root as `adopted`, and `verified` stays blocked until the root-visible gate evaluates broader proof or a bounded exception. |
| `mazer` | Repo-local adoption slice is landed. | Matrix status is explicit at root as `adopted`, and `verified` stays blocked until the root-visible gate evaluates broader proof or a bounded exception. |
| `stream` | Do the same once incubating scope is confirmed. | Matrix status is explicit and backed by a repo-local artifact or a documented defer decision. |
| `nat1-games` | Do the same once incubating scope is confirmed. | Matrix status is explicit and backed by a repo-local artifact or a documented defer decision. |
| `playbook-demo` | Decide whether it remains a demo-only mirror or a contract demonstration surface. | Matrix status is explicit and the demo role is documented. |

## Measurement

This program is not complete when the docs read well. It is complete when drift becomes measurable.

Minimum measurable outputs:

- one published adoption matrix
- one machine-readable Playbook contract reference
- one repeatable continuity promotion path
- one root-visible verification or report surface
- one explicit adoption state for every in-scope repo

## Operating Rule

ATLAS root remains the selector, router, and report surface.

Owner repos remain the owner of implementation truth.

Playbook convergence means shared contracts, shared verification, and shared principles across repos. It does not mean copying one repo into another.
