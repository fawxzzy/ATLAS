# GitHub Control-Plane Marker Denominator Audit - 2026-07-13

## Decision

The eight-unit denominator is deterministic enough to activate.

- denominator: `8`
- numerator: `6`
- percentage: `75`
- freshness timestamp: `2026-07-13T15:58:36Z`
- transition reason: marker moved from `percentage=null` because the denominator now has eight binary, authority-backed units and six of them are complete on current evidence

Evidence list:

- `docs/audits/GITHUB-CONTROL-PLANE-OPENING-AUDIT-2026-07-12.md`
- `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`
- `docs/ops/GITHUB-CONTROL-PLANE-WATCH-2026-07-13.md`
- `docs/ops/GITHUB-CONTROL-PLANE-EVENT-PROJECTION-CONTRACT-IMPLEMENTATION-2026-07-13.md`
- `docs/ops/GITHUB-CONTROL-PLANE-EVENT-ADMISSION-RUNTIME-2026-07-13.md`
- `docs/ops/GITHUB-CONTROL-PLANE-END-TO-END-NO-SEND-CANARY-2026-07-13.md`
- `runtime/codex/discordos/logs/20260713T151453726Z-discordos-github-projection-intent-dry-run-consumer/run.json`
- live GitHub PR `https://github.com/fawxzzy/DiscordOS/pull/48`
- live GitHub commit compare `3e9ca5fd67fbcc728ac42f85b4222600523c2dfe...main`

## Unit Matrix

| Unit | Binary definition of done | Authoritative evidence sources | Current status | Exact blocker when not complete | Freshness rule |
|---|---|---|---|---|---|
| `repository_inventory` | Complete only when the authoritative registry enumerates all ten governed cloud repositories plus declared local-only `stream` and remote-only `cortex`, with stable ordering and explicit endpoint states instead of inferred zeroes. | `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`, `docs/audits/GITHUB-CONTROL-PLANE-OPENING-AUDIT-2026-07-12.md`, `docs/ops/GITHUB-CONTROL-PLANE-WATCH-2026-07-13.md`, `stack.yaml` | `complete` | none | Fresh while the July 12 registry plus the July 13 watch remain the latest accepted root evidence set for inventory state. |
| `parity_projection` | Complete only when every governed checkout has separate local-tracking parity and live cloud-default parity facts, or an explicit `unknown` / `not_applicable` state for missing lanes such as remote-only or local-only components. | `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`, `docs/audits/GITHUB-CONTROL-PLANE-OPENING-AUDIT-2026-07-12.md`, live GitHub compare evidence cited in the registry | `complete` | none | Fresh while no newer accepted parity refresh supersedes the July 12 registry and the component inventory has not been redefined. |
| `actions_projection` | Complete only when workflow inventory, bounded run samples, latest observed workflow conclusions, and recovery ownership are projected without treating `no run returned` or an empty sample as green. | `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`, `docs/ops/GITHUB-CONTROL-PLANE-WATCH-2026-07-13.md`, registry `recovery_queues.ci` | `complete` | none | Fresh while the July 13 watch is the latest accepted Actions delta on top of the July 12 registry. |
| `open_work_hygiene` | Complete only when every open PR and issue in scope has one allowed evidence-backed disposition and no terminal state is inferred from age or narrative alone. | `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`, `docs/audits/GITHUB-CONTROL-PLANE-OPENING-AUDIT-2026-07-12.md`, registry `disposition_queues` | `complete` | none | Fresh while the July 12 registry dispositions remain the latest accepted open-work projection and no newer accepted hygiene receipt supersedes them. |
| `release_security_projection` | Complete only when release, branch-protection/ruleset, Dependabot, and secret-scanning states are visible or explicitly endpoint-specific `unknown` / `access_denied` / `disabled`, and the Fitness critical secret remains projected as a blocker rather than hidden. | `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`, `docs/ops/GITHUB-CONTROL-PLANE-WATCH-2026-07-13.md`, `docs/audits/GITHUB-CONTROL-PLANE-OPENING-AUDIT-2026-07-12.md` | `complete` | none | Fresh while the July 13 watch remains the newest accepted release/security delta and the registry remains the governing detailed projection. |
| `cleanup_governance` | Complete only when remote branch candidates and local worktree candidates are freshly classified with exclusions, explicit retention class, authority posture, and any required receipts, even if deletion remains unauthorized. | `docs/registry/GITHUB-CONTROL-PLANE-REGISTRY.json`, registry `cleanup_summaries`, registry per-repository `cleanup`, `docs/audits/GITHUB-CONTROL-PLANE-OPENING-AUDIT-2026-07-12.md` | `incomplete` | `local_worktree_retention_class` is still `UNKNOWN`, multiple per-worktree `retention_class` values remain `UNKNOWN`, and no fresh retention-class reconciliation receipt has cleared that blocker. | Fresh while the July 12 registry remains the latest accepted cleanup inventory; status stays incomplete until a newer accepted retention-class receipt lands. |
| `stack_event_correlation` | Complete only when `_stack` emits canonical idempotent GitHub event receipts and Atlas preserves the correlated admission and projection identities without breaking the source event chain. | `docs/ops/GITHUB-CONTROL-PLANE-EVENT-PROJECTION-CONTRACT-IMPLEMENTATION-2026-07-13.md`, `docs/ops/GITHUB-CONTROL-PLANE-EVENT-ADMISSION-RUNTIME-2026-07-13.md`, `docs/ops/GITHUB-CONTROL-PLANE-END-TO-END-NO-SEND-CANARY-2026-07-13.md`, `repos/_stack@a12922a6e2479101b90772a1c678bfd99e6ed7ae`, canary artifacts | `complete` | none | Fresh while `_stack/main` remains at `a12922a6e2479101b90772a1c678bfd99e6ed7ae` and no later accepted event-contract receipt supersedes the July 13 canary chain. |
| `discordos_projection` | Complete only when an authorized DiscordOS single-writer application consumes a GitHub projection intent, applies the sanctioned write, and returns exact live readback tied to the same event/admission/projection identities. | `docs/ops/GITHUB-CONTROL-PLANE-END-TO-END-NO-SEND-CANARY-2026-07-13.md`, `runtime/codex/discordos/logs/20260713T151453726Z-discordos-github-projection-intent-dry-run-consumer/run.json`, live GitHub PR `#48` | `incomplete` | The July 13 canary proves dry-run no-send behavior only; no authorized single-writer apply or exact live readback receipt exists yet. | Fresh while the July 13 canary remains the latest accepted DiscordOS GitHub-projection proof. Status cannot move to complete without a newer live-readback receipt. |

## Why The Denominator Is Deterministic

- Each unit now has one binary done rule that can evaluate to `complete` or `not complete` from named authority, without counting documentation volume or partial implementation.
- Unknown, denied, disabled, and blocked states stay explicit instead of being rewritten into success.
- The two incomplete units are incomplete for concrete reasons, not because the denominator is ambiguous.

## Numerator Basis

Completed units:

1. `repository_inventory`
2. `parity_projection`
3. `actions_projection`
4. `open_work_hygiene`
5. `release_security_projection`
6. `stack_event_correlation`

Incomplete units:

1. `cleanup_governance`
2. `discordos_projection`

## Marker Consequence

The GitHub Control-Plane Integration marker is now authorized to move from `null` to `75%` on the exact `6 / 8` basis above.

This audit does not move `Atlas Full-System Re-evaluation`; that audit-gate marker remains `50%`.

## Verification

- Initiative continuity JSON parses successfully after the marker and phase-state update.
- `python ops/validation/validate_stack.py --ratchet --output-dir tmp/validation/github-e2e-canary-marker-audit` now reports `critical=0 error=0 warning=28 info=0`.
- `git diff --check` passes.
- The governed repo-visible change set remains the four requested paths:
  - `docs/ops/GITHUB-CONTROL-PLANE-END-TO-END-NO-SEND-CANARY-2026-07-13.md`
  - `docs/ops/GITHUB-CONTROL-PLANE-MARKER-DENOMINATOR-AUDIT-2026-07-13.md`
  - `docs/memory/initiatives/initiative-github-control-plane-integration.json`
  - `docs/atlas-book/02-lanes-and-markers.md`
