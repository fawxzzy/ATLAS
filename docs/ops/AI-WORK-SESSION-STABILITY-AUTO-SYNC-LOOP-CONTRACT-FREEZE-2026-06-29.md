# AI Work Session Stability Auto-Sync Loop Contract Freeze

- CODEX-MSG-ID: `CODEX-2026-06-29-AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-CONTRACT-FREEZE`
- Date: `2026-06-29`
- Scope: `ATLAS-root docs-only contract freeze`
- Marker: `AI Work Session Stability & Auto-Sync Loop`
- Initial percent: `0%`
- Marker type: `supporting open marker`

## Problem Statement

ATLAS now has enough root, owner-repo, QA, Playbook, Cortex, marker, and continuity surfaces that AI work can create drift when each session relies on operator memory instead of a required start and close loop. The immediate failure mode is not missing doctrine. The failure mode is fragmented enforcement: root validation, stack lock, published inventory, Book projections, continuity manifests, QA readiness, owner-repo status, Playbook doctrine, and platform-linked state can all be correct in isolation while the session as a whole does not prove they were checked together.

This receipt opens one supporting marker to make that loop explicit before any tool is implemented.

## Why This Is New Scope

This is not a reopened closed ratchet. `Truth Map & ATLAS Book` remains closed because the earlier continuity rollup and restart-surface work are still valid. `Inventory & Truth Map` remains held at `99%` because projection freshness is not fully automated. The new marker covers a different operating concern: every AI/Codex/ChatGPT work session must be forced to check, classify, and close against the relevant ATLAS components it depends on.

## Evidence That Opens The Marker

- The research pass `CODEX-2026-06-29-ATLAS-TECH-STACK-STABILITY-AND-COMPONENT-UTILIZATION-RESEARCH-PACKET` found that current workflows work but are fragmented.
- Root validation during this packet still reports `critical=0 error=0 warning=3 info=0`.
- Continuity health during this packet reports `19 ok / 0 warning / 0 error`.
- Continuity coverage during this packet reports `pending_review_count=0`, `eligible_open_marker_count=6`, `open_marker_restart_ready_count=6`, and `maintained_manifest_restart_ready_count=19`.
- The operational root branch is `codex/atlas-root-mazer-dirty-head-resync` at `dd9dab84c0589cb9f68868b8e20ad93139b7f508`, still `18` commits ahead of `origin/main`.
- Preflight found pre-existing local generated drift in `stack.lock.yaml`, `docs/registry/STACK-REPO-INVENTORY.json`, and `docs/audits/STACK-REPO-INVENTORY.md` because `repos/mazer` had already advanced to `c48d38a69d84198c2763d04bc633339b7ce952e3`. This packet does not stage or own that residue.
- Fitness release readiness remains constrained by physical/manual proof and missing BrowserStack credentials.
- Playbook is useful doctrine but not yet a mandatory per-session enforcement surface.
- No single current command answers whether an AI work session is safe to start and safe to close.

## Non-Claims

- This receipt does not implement the loop.
- This receipt does not mutate owner repos.
- This receipt does not mutate Supabase or Vercel.
- This receipt does not deploy, publish, or alter release-readiness outputs manually.
- This receipt does not close the Fitness release gate.
- This receipt does not close Sandbox Simulation Readiness.
- This receipt does not move existing markers.
- This receipt does not stage the pre-existing generated stack lock or inventory writeback.

## Required AI Work Session Loop

1. Pre-work read phase: read root `AGENTS.md`, the workflow profile, current Book state, marker table, receipt index, restart guide, stack lock, inventory, and relevant owner truth surfaces.
2. Root/owner scope classification: decide whether the session is stack-root governance, owner-repo work, platform work, or read-only research.
3. Marker board read: run the marker selector and identify held lanes, admissible lanes, and no-movement constraints.
4. Playbook/doctrine check: confirm whether repo-local Playbook doctrine or adoption contracts are relevant.
5. Stack lock/inventory freshness check: compare live owner repo heads, `stack.lock.yaml`, published inventory, and Book projection references.
6. QA/release-readiness check: read release readiness, release rehearsal, manual attestation, provider readiness, and secret-readiness surfaces when release state is implicated.
7. Continuity manifest check: run manifest health, open-marker restart index, and continuity coverage.
8. Protected-surface check: block accidental touch of `archive/`, `.playwright-mcp/`, `.vercel`, `.env*`, `secrets/`, broad untracked backlog, owner repos, deploy surfaces, and platform mutation surfaces unless explicitly authorized.
9. Execution: perform only the admitted lane work.
10. Proof/validation: run the lane-local proof commands and root validation.
11. Projection freshness check: recheck whether touched truth surfaces require Book, manifest, inventory, or selector refresh.
12. Receipt/restart update: write the durable receipt and update mirrors only when the work changed restart truth.
13. Marker decision: move markers only when the marker ratchet threshold is met.
14. Commit/push/parity: stage exact admitted files only, commit intentionally, push, fetch, and confirm branch parity.
15. Handoff summary: report done/now/next, residue, blockers, validation, marker state, and next exact package.

## Required Future Tool Family

- `ops/atlas/ai_work_session_preflight.py`
- `ops/atlas/ai_work_session_closeout.py`
- `ops/atlas/projection_freshness.py`
- `ops/atlas/component_utilization_audit.py`
- `ops/atlas/playbook_adoption_matrix.py`

## First Implementation Slice

The first implementation slice is a read-only `ops/atlas/ai_work_session_preflight.py` command. It must collect existing health checks, classify scope, detect projection freshness drift, list open markers, list release gates, list Playbook adoption signals, and list protected residue. It must not mutate owner repos, stage files, commit, deploy, or write output unless `--output` is provided. It should return nonzero only for true blockers or explicit `--strict`.

## Marker Movement Thresholds

- `0%`: contract opened.
- `10%`: required loop contract frozen.
- `25%`: preflight aggregator implemented and test-backed.
- `40%`: closeout aggregator implemented and test-backed.
- `55%`: projection freshness check implemented and test-backed.
- `70%`: Playbook adoption matrix implemented and test-backed.
- `85%`: loop used across ATLAS root plus at least two owner repos.
- `100%`: loop is required, documented, restart-safe, and standard across active stack workflows.

## What Must Not Move The Marker

- Wording cleanup alone.
- One-off manual checklists.
- Stale-doc edits.
- Owner-repo work that does not use the loop.
- Platform checks without automation.
- Runtime latest-file refresh without a stable session contract.
- Closed-ratchet narration.

## Exact Next Package

`AI Work Session Stability & Auto-Sync Loop read-only preflight aggregator first-implementation admission`

