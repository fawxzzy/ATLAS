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

## Current Live Posture

Treat the long doctrine handoff as constitutional guidance, not as a literal implementation status board.

The still-authoritative rules are unchanged:

- root is the control plane and child repos stay independent
- root federates owner truth instead of duplicating it
- transcript residue is not canonical memory
- Verta stays visible, untrusted, and metadata-only
- voice remains intentionally deprioritized unless explicitly chosen

The current landed state from this workspace is:

- cockpit is landed as a thin read-only operator surface
- Playbook owner export is landed
- root read-only consumption is landed
- continuity and historical query coverage are landed
- reviewed Verta derivative notes are landed without changing trust posture
- `fitness` is `verified` for a bounded `verification_scope=targeted`
- `mazer` is `verified` for a bounded `verification_scope=targeted`

The active next move is therefore not more root product plumbing. It is stack-wide source-verified synergy discovery before any shared implementation lane, with Atlas/Fitness as tranche 1 rather than the whole frontier.

## Next Cross-App Synergy Discovery Lane

Cross-app synergy is now the next active widening lane at the stack level, not just a two-repo program. The reviewed PDF stayed out of live posture while it lacked direct repo, Drive, chat, and Playbook access. That was the right trust posture then. Now that source access exists and the Mazer verification frontier is closed, the correct next move is source-verified discovery rather than more strategy prose.

Owner-surface scope for the first wave is explicit:

- `lifeline` owns approvals, receipts, and capability semantics and must be searched early for implicit stack-wide contracts that should become explicit owner truth
- `playbook` owns governance, verification, and workflow-pack reuse surfaces
- `_stack` owns orchestration, merge, resume, and worker contracts
- `atlas` owns doctrine, UAPI, and platform contracts
- Atlas/Fitness remains the first concrete telemetry-first pairing, not the whole frontier

Operating rules carried forward:

- share contracts before sharing implementations
- run risky integrations in shadow mode before cutover
- keep unified auth behind telemetry hygiene, support tooling, and account-model stabilization

Sequencing for the next lane:

1. build a source-verified synergy registry across `repos/**` for surfaces that already behave shared but still lack an explicit owner, contract, or package
2. run a first-wave owner-surface discovery pass across Lifeline, Playbook, `_stack`, and Atlas owner lanes
3. use Atlas/Fitness as the first concrete telemetry-first tranche for shared glossary and event-contract discovery
4. freeze the canonical noun glossary and the top shared event contracts before sharing implementation
5. instrument Atlas against those contracts
6. instrument Fitness against those contracts
7. rank second-wave repos by duplication, shared nouns, active initiative pressure, and contract absence
8. extract reusable workflow or warehouse checks only after the contract lane is frozen
9. defer unified auth until telemetry and the account model are stable
10. defer shared UI until token ownership, package boundaries, and publishing are explicit
11. defer cross-sell until identity and attribution exist
12. defer shared data or ML until the earlier layers are real and verifiable

This lane starts as discovery truth grounded in visible source material. Live posture still changes only when owner-repo evidence exists and the root can project it read-only without reinterpretation.

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

Phases 1 through 3 are materially landed in the current workspace. The active program edge is Phase 4 and selective widening inside Phase 5, now that both current vertical application fixtures have bounded repo-owned verification truth.

### Phase 1: Posture Lock

Acceptance criteria:

- the root doctrine says this is a convergence program, not a root merge
- the adoption matrix is evidence-based and explicitly provisional until repo-local verification lands
- cockpit remains a read-only client surface rather than a second truth store

Primary slices:

- landed: stack root PR published this roadmap and the adoption matrix
- landed: stack root artifacts made the program queryable by initiatives and plans

### Phase 2: Contract Extraction

Acceptance criteria:

- Playbook principles and pattern checks are addressable outside prose
- root context-pack routing can pull contract refs by intent
- repo-local verify flows can report which contract version they target

Primary slices:

- landed: Playbook repo exported the canonical principles, patterns, and checklist contract
- landed: stack root routing and roadmap refs point at the exported contract artifact

### Phase 3: Continuity Lane

Acceptance criteria:

- serious sessions produce a structured handoff instead of relying on transcript scraping
- imported chat or archive material is cataloged as traceability evidence, not mistaken for doctrine
- promotion from handoff or archive into initiative, memory, knowledge, and receipt lanes is documented and repeatable

Primary slices:

- landed: stack root standardized a structured conversation-handoff authoring flow on top of the existing handoff contract
- landed: continuity manifests, promotion routing, and historical query coverage are visible from root
- landed: reviewed derivative-note promotion now covers the partial historical questions already processed
- next only where useful: continue reviewed-note promotion for partial or missing historical answers, not as a general documentation binge

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
- `verified` requires scoped repo-owned verification truth and an honest root projection; broader product certification remains out of scope
- the stack can report both convergence status and conversation-continuity health from saved artifacts
- repo-local rollout remains scoped to the owning repo

Primary slices:

- application repo PRs: widen only where the next repo-local adoption or verification slice creates real operator leverage
- stack root PR: keep projecting landed repo-local adoption and verification evidence read-only into awareness and cockpit
- only then: widen into additional repo-local waves where the next operator constraint actually depends on them
- only after that frontier is stable: continue widening the deferred cross-app synergy lane from the registry and telemetry end, not from auth or ML

## First Repo-Local PR Slices

| Surface | First Slice | Done When |
| --- | --- | --- |
| `playbook` | Export canonical Playbook principles and checks as a human spec plus machine-readable contract. | Root docs and repo-local verify can reference one contract version and one contract path. |
| `lifeline` | Align approval, receipt, and execution surfaces to the shared contract. | Lifeline docs or verify output can show which Playbook contract version is implemented. |
| `_stack` | Align worker merge, resume, and orchestration patterns to the shared contract. | Resume and merge flows cite the contract and verification is explicit. |
| `atlas` | Pull contract refs and continuity refs by intent instead of broad context dumps. | Context or awareness surfaces can retrieve the right contract and continuity artifacts deterministically. |
| `fitness` | Repo-local adoption and targeted verification slices are landed. | Matrix status is explicit at root as bounded `verified` with `verification_scope=targeted`, without implying broader product certification. |
| `mazer` | Repo-local adoption and targeted verification slices are landed. | Matrix status is explicit at root as bounded `verified` with `verification_scope=targeted`, without implying broader product certification. |
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
