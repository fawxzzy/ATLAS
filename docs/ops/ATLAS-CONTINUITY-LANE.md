# ATLAS Continuity Lane

This runbook defines the stack-owned continuity lane for serious Codex and ChatGPT work.

It turns useful session output into structured, promotable artifacts without treating raw transcript history as canonical memory.

## Purpose

The continuity lane exists so ATLAS can keep compounding prior work across sessions while preserving the existing ownership split:

- owner repos keep owner truth
- root coordinates, routes, and promotes
- transcripts remain traceability, not doctrine

This is a root-owned coordination surface. It does not create a second truth store for child repos.

## Contract Surface

Structured handoffs use:

- schema: `schemas/atlas.continuity.handoff.v1.json`
- storage path: `runtime/receipts/handoffs/**`

Continuity source inventory uses:

- schema: `schemas/atlas.continuity.source.manifest.v1.json`
- loader: `ops/atlas/continuity.py`
- source typing: imported docs/PDFs, promotion notes, handoffs, reviews, and residue stay distinguishable in manifest-backed query results
- historical query preference: reviewed derivative notes first, then existing promotion notes, then grounded docs and handoffs, then import metadata
- read-only slices:
  - `continuity_source_inventory`
  - `continuity_promotion_queue`
  - `continuity_source_groups`
  - `continuity_search_status`
  - `continuity_historical_query_coverage`
  - `continuity_coverage`

Related existing surfaces:

- `docs/architecture/CODEX-HANDOFF-CONTRACT.md` for Codex task-output capture
- `docs/ops/ATLAS-CONVERSATION-RUNBOOK.md` for grounded conversation manifests and turns
- `docs/knowledge/PROMOTION-RUNBOOK.md` for durable knowledge promotion
- `docs/architecture/ATLAS-RETENTION-AND-MEMORY-POLICY.md` for transcript and retention posture

## Continuity Layers

ATLAS continuity uses three layers.

### 1. Raw traceability

Raw chat exports, PDFs, notes, and imported planning material remain evidence first.

Typical paths:

- `data/imports/knowledge/**`
- external files staged for import under `data/**`
- local-only scratch material under `tmp/**`

Rules:

- raw artifacts may be retained for provenance
- raw artifacts are not canonical memory by themselves
- raw artifacts must keep trust posture explicit

### 2. Structured handoff

Every serious work session should emit one structured handoff artifact with:

- durable facts
- decisions and rationale
- next PR-sized actions
- open questions
- risks
- promotion targets
- transcript references marked `trace_only`

Rules:

- serious sessions should not end as transcript-only residue
- handoffs must validate against `atlas.continuity.handoff.v1`
- handoffs belong in runtime, not repo roots

### 3. Promotion

Stable outcomes are promoted into the owning durable lane:

- initiative and plan state -> `docs/memory/**`
- durable decisions -> `docs/memory/decisions/**`
- durable knowledge -> `docs/knowledge/**`
- execution evidence and receipts -> `runtime/receipts/**` or repo-local receipt surfaces

Promotion rules:

- promote only validated, durable outputs
- prefer owner-repo promotion when the fact belongs to a child repo
- keep source lineage explicit
- do not auto-promote raw imports or transcript residue
- historical-planning answers should resolve to grounded source hits or an explicit gap, never transcript memory alone
- reviewed derivative notes may summarize selected Verta historical sources without changing Verta archive trust posture

## Authoring Flow

1. Ground the session on current awareness, memory, repo, and contract state.
2. Emit one `atlas.continuity.handoff.v1` artifact under `runtime/receipts/handoffs/`.
3. Review the handoff for durable facts, decisions, next actions, and questions.
4. Promote approved items into `docs/memory/**`, `docs/knowledge/**`, or the owner repo.
5. Leave transcript references as trace-only links, not as the durable endpoint.

## Promotion Routing

Use this routing by default:

| Artifact Type | Default Target |
| --- | --- |
| active multi-session objective | `docs/memory/initiatives/*.json` |
| ordered execution work | `docs/memory/plans/*.json` |
| accepted stack decision | `docs/memory/decisions/*.json` |
| reusable cross-session knowledge | `docs/knowledge/**` |
| execution or review evidence | `runtime/receipts/**` or repo-local receipt lane |
| repo-specific doctrine or contract | owning repo, not ATLAS root |

## Trust And Ownership Rules

- Visibility does not imply trust.
- Promotion does not change repo ownership.
- Root may summarize or reference child-repo truth, but it must not duplicate it.
- If a durable fact belongs to `playbook`, `lifeline`, `_stack`, `atlas`, or an application repo, the promoted endpoint should point to the owner surface.

## Verification

Minimum continuity checks:

- handoff JSON validates against `schemas/atlas.continuity.handoff.v1.json`
- `transcript_role` is always `trace_only`
- every serious handoff names at least one repo or initiative ref
- next actions are PR-sized and owner-routed
- promoted outputs retain source refs back to the handoff or imported evidence

Suggested validation command:

```powershell
python .\ops\validation\validate_stack.py
```

## Anti-Patterns

- treating transcripts as durable memory
- dropping durable facts only into chat summaries
- copying child-repo contracts into root for convenience
- storing serious handoffs in repo roots
- promoting unvalidated archive content directly into doctrine
