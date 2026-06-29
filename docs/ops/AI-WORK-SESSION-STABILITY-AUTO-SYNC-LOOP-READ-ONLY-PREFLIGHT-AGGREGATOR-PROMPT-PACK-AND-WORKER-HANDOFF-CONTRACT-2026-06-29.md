# AI Work Session Stability Auto-Sync Loop Read-Only Preflight Aggregator Prompt-Pack And Worker Handoff Contract

- Date: `2026-06-29`
- Lane: `AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator prompt-pack and worker handoff contract`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `freeze the exact future worker objective, inherited contract spine, output/report contract, proof matrix, allowed-touch surfaces, forbidden-touch surfaces, no-mutation guards, and stop conditions for the first read-only ai_work_session_preflight worker without implementing it`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/memory/initiatives/continuity-manifest-ai-work-session-stability-auto-sync-loop.json`
  - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-CONTRACT-FREEZE-2026-06-29.md`
  - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-READ-ONLY-PREFLIGHT-AGGREGATOR-FIRST-IMPLEMENTATION-ADMISSION-2026-06-29.md`
  - `ops/atlas/marker_knockout_selector.py`
  - `ops/atlas/continuity_manifest_health.py`
  - `ops/atlas/continuity_open_marker_restart_index.py`
  - `ops/atlas/continuity_coverage.py`
  - `ops/validation/validate_stack.py`
- Control-plane checkpoint: `codex/atlas-root-mazer-dirty-head-resync@81e2a38f`

## Objective

Freeze the exact handoff for the first future implementation worker so `ops/atlas/ai_work_session_preflight.py` can be built later without reopening contract ambiguity around scope classification, output shape, read-only limits, protected-surface rules, owner/platform boundaries, or stop behavior.

This pass does not:

- implement `ops/atlas/ai_work_session_preflight.py`
- implement `tests/test_atlas_ai_work_session_preflight.py`
- implement any closeout worker, projection-refresh worker, or enforcement wrapper
- move the marker above `10%`
- mutate owner repos, Supabase, Vercel, `secrets/`, `.env*`, `.playwright-mcp/`, `archive/`, or protected runtime surfaces
- stage files, commit owner repos, deploy, publish, or clear the protected Fitness blocker family

## Inherited Contract Spine

The opening contract and first-implementation admission already froze:

- the required manual AI-session start and close loop
- the first admitted read-only preflight slice
- the structured JSON report contract boundary
- the strict exit semantics
- the bounded root-relative output-path rule
- the explicit no-side-effects guard

This packet inherits those boundaries and freezes the exact worker handoff that the future implementation must obey.

## Future Worker Objective

Implement one read-only root-owned preflight aggregator that answers:

`Is this AI work session safe to start, and what ATLAS components must be checked or refreshed before or after the work?`

Expected future implementation files:

- `ops/atlas/ai_work_session_preflight.py`
- `tests/test_atlas_ai_work_session_preflight.py`

## Exact Allowed Worker Behavior

The future worker may:

1. read ATLAS-root git branch, HEAD, parity, and dirty-state posture
2. read marker selector output and current marker posture
3. read continuity manifest health, open-marker restart index, and continuity coverage
4. read stack-lock and published inventory truth
5. compare authoritative owner-head truth against projected lock or inventory mirrors
6. read QA or release-readiness summary surfaces when the selected scope implicates release state
7. read Playbook adoption or doctrine-hint surfaces when relevant
8. summarize protected-surface residue classes
9. summarize owner-repo status read-only when owner scope is explicitly selected
10. summarize platform readiness read-only when platform scope is explicitly selected
11. emit one deterministic stdout summary and one deterministic JSON payload
12. write JSON only when `--output <root-relative-path>` is explicitly provided and admitted

## Exact Forbidden Worker Behavior

The future worker may not:

- mutate owner repos
- mutate Supabase
- mutate Vercel
- deploy or publish
- stage, commit, push, or fetch
- write runtime latest files by implication
- modify Book, manifest, selector, receipt, or lane surfaces
- generate receipts automatically
- move markers
- touch protected surfaces
- treat projected sources as authoritative truth
- widen from read-only inspection into orchestration or enforcement

## Exact CLI Contract

Required future flags:

- `--json`
- `--scope root|owner|platform|research`
- `--owner <name>` as read-only classification input only
- `--strict`
- `--output <root-relative-path>`

Required default behavior:

- default to read-only
- default to stdout summary plus deterministic JSON on stdout
- do not write files unless `--output` is provided
- preserve deterministic output ordering

## Exact JSON Output Contract

The future worker must emit one JSON object with these top-level fields:

- `schema_version`
- `status`
- `scope`
- `root`
- `branch`
- `head`
- `remote_tracking`
- `parity`
- `validation`
- `markers`
- `continuity`
- `stack_inventory`
- `projection_freshness`
- `qa_release_readiness`
- `playbook`
- `platform`
- `protected_surfaces`
- `local_residue`
- `required_followups`
- `blockers`
- `warnings`

Contract notes:

- `status` must stay bounded to the already-admitted status classes
- `projection_freshness` must distinguish authoritative truth from projected drift
- `platform` stays read-only and may degrade to placeholder or unavailable classification
- `required_followups` must name exact next actions rather than generic prose
- `blockers` and `warnings` must be stable machine-readable finding arrays

## Exact Exit-Code Policy

- default mode:
  - `0` for `ok`
  - `0` for `advisory_drift`
  - `2` for `blocker`
  - `3` for `internal_error`
- `--strict` mode:
  - `0` for `ok`
  - `1` for `advisory_drift`
  - `2` for `blocker`
  - `3` for `internal_error`

No broader exit taxonomy is admitted in the first worker slice.

## Exact Scope-Classification Logic

The future worker must classify one session as:

- `root`
- `owner`
- `platform`
- `research`

Classification rules:

- `root` means ATLAS-root governance, mirrors, manifests, selectors, validation, or stack-read work
- `owner` means a named owner repo is implicated, but status collection remains read-only
- `platform` means Supabase or Vercel state is implicated, but status collection remains read-only
- `research` means observational work with no mutation or release consequence
- fail closed when scope cannot be classified from admitted inputs

## Exact Read-Only Check Families

The future worker must call or summarize:

1. git branch, HEAD, remote tracking, and parity
2. `python .\ops\atlas\marker_knockout_selector.py --format json`
3. `python .\ops\atlas\continuity_manifest_health.py`
4. `python .\ops\atlas\continuity_open_marker_restart_index.py`
5. `python .\ops\atlas\continuity_coverage.py`
6. stack inventory freshness comparison
7. `stack.lock.yaml` comparison against current live working set
8. Atlas Book projection freshness cues
9. QA or release-readiness summary surfaces when implicated
10. Playbook adoption signal checks when implicated
11. owner-repo status summary when owner scope is selected
12. optional read-only platform status placeholders when platform scope is selected
13. protected-surface residue summary

## Exact Guards

No-mutation guard:

`The AI work-session preflight worker may read admitted root, owner-head, continuity, marker, inventory, QA, doctrine, and optional platform-status surfaces; classify scope, projection drift, residue, warnings, blockers, and required follow-ups; and render one deterministic summary plus one deterministic JSON payload, but it may not mutate git state, mutate owner repos, mutate platform state, refresh projections automatically, write runtime latest files by implication, stage files, commit, deploy, publish, move markers, or treat projected sources as authoritative truth.`

No-owner-repo-mutation guard:

`Owner scope stays read-only. The worker may inspect repo status, branch, HEAD, and selected truth-owner surfaces, but it may not edit files, install dependencies, run repo migrations, or perform owner-side proof actions.`

No-platform-mutation guard:

`Platform scope stays read-only. The worker may classify Supabase or Vercel readiness from admitted status surfaces only; it may not change config, deploy, write data, alter auth, or invoke mutation-bearing connectors.`

## Exact Stop Conditions

The future worker must stop and return a blocker when:

- authoritative branch or parity truth is unavailable
- required authoritative marker or continuity truth is unavailable
- authoritative truth contradicts itself in a way that blocks evaluation
- the requested scope cannot be classified safely
- the requested output path is absolute or protected
- owner or platform mutation would be required to answer the question honestly
- protected surfaces would need to be touched

## Exact Proof Matrix

The future worker packet must later prove at least:

1. root-scope clean read
2. root-scope advisory projection drift
3. owner-scope read-only classification
4. platform-scope read-only classification
5. research-scope read-only classification
6. protected output-path rejection
7. contradictory authoritative-source failure
8. strict-mode advisory nonzero exit
9. blocker exit
10. internal-error exit
11. deterministic ordering of summary and JSON fields

## Exact Next Package

`AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator implementation-readiness closeout and worker-routing`

Why:

- the worker objective is now frozen
- the report contract and exit policy are now frozen
- allowed-touch and forbidden-touch surfaces are now frozen
- the next honest docs-only step is to decide whether the first worker can be routed without opening broader implementation or mutation ambiguity

## Ratchet Decision

Ratchet:

- `AI Work Session Stability & Auto-Sync Loop` stays at `10%`

Why:

- this pass freezes worker handoff discipline, not new executed state
- no tool implementation landed
- no proof-backed adoption widened
- no blocker family was cleared beyond the already-landed first-admission threshold

## Validation Note

Live proof during this packet reads:

- `python .\ops\atlas\marker_knockout_selector.py --format json`
  - active lane still held at `Sandbox Simulation Readiness`
  - supporting AI work-session lane still at `10%`
  - AI fallback packet now points to `AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator implementation-readiness closeout and worker-routing`
- `python .\ops\atlas\continuity_manifest_health.py`
  - `20 ok / 0 warning / 0 error`
- `python .\ops\atlas\continuity_open_marker_restart_index.py`
  - `7 / 7` eligible open markers restart-ready
- `python .\ops\atlas\continuity_coverage.py`
  - `status: structured`
  - `pending_review_count: 0`
- `python .\ops\validation\validate_stack.py`
  - `critical=0 error=0 warning=3 info=0`

## Rule

`Worker Handoff Before Worker Routing`

The first read-only preflight worker may not be routed for implementation until its exact objective, report contract, read-only boundary, proof matrix, and stop conditions are frozen tightly enough that later code cannot widen the lane through prompt drift.

## Pattern

contract freeze -> first-implementation admission -> prompt-pack and worker handoff contract -> implementation-readiness closeout and worker-routing -> bounded worker landing

## Failure Mode

`Handoff Drift Before Implementation`

The lane fails if the future worker is implemented from memory or evolving prose, so that scope classification, output shape, stop behavior, or mutation limits change between the admitted first slice and the actual worker landing.
