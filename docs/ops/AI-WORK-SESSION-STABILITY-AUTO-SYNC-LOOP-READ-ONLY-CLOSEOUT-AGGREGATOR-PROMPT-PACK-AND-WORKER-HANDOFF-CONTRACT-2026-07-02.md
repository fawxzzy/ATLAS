# AI Work Session Stability Auto-Sync Loop Read-Only Closeout Aggregator Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-02-AI-WORK-SESSION-CLOSEOUT-AGGREGATOR-PROMPT-PACK`
- Date: `2026-07-02`
- Lane: `AI Work Session Stability & Auto-Sync Loop read-only closeout aggregator prompt-pack and worker handoff contract`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `freeze the exact future worker objective, output contract, proof matrix, allowed-touch surfaces, forbidden-touch surfaces, stop conditions, and reconciliation route for the first read-only ai_work_session_closeout worker without implementing it`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/memory/initiatives/continuity-manifest-ai-work-session-stability-auto-sync-loop.json`
  - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-POST-OWNER-LANE-SEPARATION-NEXT-SLICE-SELECTION-2026-07-02.md`
  - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-READ-ONLY-CLOSEOUT-AGGREGATOR-FIRST-IMPLEMENTATION-ADMISSION-2026-07-02.md`
  - `ops/atlas/marker_knockout_selector.py`
  - `ops/atlas/continuity_manifest_health.py`
  - `ops/atlas/continuity_open_marker_restart_index.py`
  - `ops/atlas/continuity_coverage.py`
  - `ops/validation/validate_stack.py`
- Control-plane checkpoint: `main@d919eaca`

## Objective

Freeze the exact handoff for the first future closeout worker so `ops/atlas/ai_work_session_closeout.py` can be built later without ambiguity around closeout status, safe-stop truth, residue reporting, marker decisions, next-action routing, owner/platform boundaries, or proof requirements.

This pass does not:

- implement `ops/atlas/ai_work_session_closeout.py`
- implement `tests/test_atlas_ai_work_session_closeout.py`
- mutate Fitness, Mazer, DiscordOS, or any other owner repo
- run protected BrowserStack proof
- mutate Supabase, Vercel, deployment, secrets, `.env*`, `.playwright-mcp/`, `archive/`, or protected runtime surfaces
- move any marker
- mark PR #105 ready

## Inherited Contract Spine

The July 2 selector and admission receipts already froze:

- the closeout aggregator as the next smallest honest AI Work Session slice
- the future worker output schema
- read-only default behavior
- no owner/platform/protected mutation
- the requirement that marker movement waits for implementation and proof

This prompt-pack freezes the implementation handoff so the future worker does not widen from structured closeout reporting into orchestration.

## Future Worker Objective

Implement one read-only root-owned closeout aggregator that answers:

`Is this AI work session safe to close, what changed, what remains blocked, what proof exists, what residue remains, and what is the next exact action?`

Expected future implementation files:

- `ops/atlas/ai_work_session_closeout.py`
- `tests/test_atlas_ai_work_session_closeout.py`

## Exact Allowed Worker Behavior

The future worker may:

1. read ATLAS-root git branch, HEAD, upstream parity, staged files, unstaged files, and untracked files
2. read marker selector output and current marker posture
3. read continuity manifest health, open-marker restart index, and continuity coverage
4. read the latest stack validation receipt and summarize critical/error/warning/info counts
5. read stack inventory summary and classify dirty repos as root-blocking or advisory from current inventory truth
6. read known runtime validation receipt paths
7. read owner-repo status only when explicitly requested and only as read-only summary
8. report protected-surface touch or risk classes without touching protected surfaces
9. report whether the current session appears safe to close
10. report exact required follow-ups and one next exact action
11. emit deterministic human-readable summary output
12. emit deterministic JSON output
13. write JSON only when `--output <root-relative-path>` is explicitly supplied and admitted

## Exact Forbidden Worker Behavior

The future worker may not:

- mutate owner repos
- mutate Supabase or Vercel
- deploy, publish, or trigger protected proof
- stage, commit, push, fetch, merge, or change branches
- write runtime latest files by default
- modify Book, manifests, selector, receipts, tests, or code
- generate receipts automatically
- move markers
- clean residue
- touch protected surfaces
- treat projected docs as authoritative over live git or validation truth
- report merge/readiness/protected-proof success without evidence

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
- fail closed when critical truth cannot be read

## Exact JSON Output Contract

The future worker must emit one JSON object with these top-level fields:

- `schema_version`
- `status`
- `generated_at`
- `scope`
- `branch`
- `head`
- `remote_tracking`
- `parity`
- `changes`
- `touched_repos`
- `commands`
- `validation`
- `markers`
- `continuity`
- `inventory`
- `blockers`
- `warnings`
- `local_residue`
- `protected_surfaces`
- `owner_repo_scope`
- `platform_scope`
- `safe_to_close`
- `required_followups`
- `next_action`

Contract notes:

- `status` stays bounded to `ok`, `advisory_drift`, `blocker`, or `internal_error`
- `safe_to_close` must be false when blocking validation errors, unexplained staged files, protected-surface touch, or required owner/platform mutation exists
- `next_action` must be exact enough to paste into the next Codex or operator packet
- `markers.changed` must stay empty unless a receipt-backed ratchet threshold was actually met
- `inventory` must distinguish root-blocking dirt from advisory/non-root-blocking owner-lane dirt

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

## Exact Read-Only Check Families

The future worker must inspect or summarize:

1. root branch, HEAD, remote tracking, parity, staged diff names, unstaged diff names, and untracked file names
2. `python .\ops\atlas\marker_knockout_selector.py --format json`
3. `python .\ops\atlas\continuity_manifest_health.py`
4. `python .\ops\atlas\continuity_open_marker_restart_index.py`
5. `python .\ops\atlas\continuity_coverage.py`
6. latest `runtime/receipts/validation/stack-validation.latest.json` if present
7. `docs/registry/STACK-REPO-INVENTORY.json`
8. protected-surface path classes
9. owner-repo status summaries only when explicitly requested
10. current next-package ladder for the active lane and first fallback lane

## Exact Guards

No-mutation guard:

`The AI work-session closeout worker may read admitted root, continuity, marker, validation, inventory, residue, protected-surface, and optional owner/platform status surfaces; classify closeout status, blockers, warnings, local residue, marker posture, safe-to-close truth, required follow-ups, and next action; and render one deterministic summary plus one deterministic JSON payload, but it may not mutate git state, mutate owner repos, mutate platform state, refresh projections automatically, write runtime latest files by implication, stage files, commit, deploy, publish, move markers, or treat projected sources as authoritative truth.`

No-owner-repo-mutation guard:

`Owner scope stays read-only. The worker may inspect repo status, branch, HEAD, and selected truth-owner surfaces, but it may not edit files, install dependencies, run repo migrations, stage files, commit, push, or perform owner-side proof actions.`

No-platform-mutation guard:

`Platform scope stays read-only. The worker may classify Supabase, Vercel, BrowserStack, or GitHub Actions readiness from admitted status surfaces only; it may not change config, deploy, write data, alter auth, create secrets, rotate secrets, or invoke mutation-bearing connectors.`

## Exact Stop Conditions

The future worker must return `blocker` when:

- authoritative root branch or parity truth is unavailable
- marker selector output cannot be read
- continuity health cannot be read
- validation has `critical` or `error` for a readiness claim
- unexplained staged files exist
- protected surfaces are staged or touched
- owner or platform mutation would be required to answer honestly
- the requested output path is absolute, outside the root, or protected
- the requested scope cannot be classified safely

## Exact Proof Matrix

The future worker packet must later prove at least:

1. clean root closeout returns `ok`
2. advisory owner-lane dirt returns `advisory_drift`
3. root-blocking dirt returns `blocker`
4. validation error returns `blocker`
5. staged files are reported and block safe close unless explicitly expected
6. protected output path is rejected
7. owner scope remains read-only
8. platform scope remains read-only
9. strict mode maps advisory drift to exit code `1`
10. deterministic JSON field order and summary output
11. marker movement remains empty without receipt-backed ratchet evidence
12. exact next action is emitted for held Sandbox plus AI Work Session fallback

## Exact Next Package

`AI Work Session Stability & Auto-Sync Loop read-only closeout aggregator implementation-readiness closeout and worker-routing`

Why:

- the worker objective is now frozen
- the output contract and exit policy are now frozen
- allowed-touch and forbidden-touch surfaces are now frozen
- the next honest docs-only step is to decide whether the first worker can be routed without opening broader implementation or mutation ambiguity

## Ratchet Decision

Ratchet:

- `AI Work Session Stability & Auto-Sync Loop` stays at `25%`

Why:

- this pass freezes worker handoff discipline, not executed worker state
- no tool implementation landed
- no proof-backed adoption widened
- no blocker class was cleared beyond the already-landed first-admission threshold

## Rule

`Closeout Contract Before Closeout Worker`

The first read-only closeout worker may not be routed for implementation until its exact objective, output contract, read-only boundary, proof matrix, and stop conditions are frozen tightly enough that later code cannot widen the lane through prompt drift.

## Pattern

contract freeze -> first-implementation admission -> prompt-pack and worker handoff contract -> implementation-readiness closeout and worker-routing -> bounded worker landing

## Failure Mode

`Closeout Worker Scope Creep`

The lane fails if the closeout worker becomes an orchestration or cleanup command. Its first implementation must only report safe-close truth, residue, blockers, validation, marker posture, and next action.
