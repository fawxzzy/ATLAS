# AI Work Session Stability Auto-Sync Loop Projection Freshness Checker Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-02-AI-WORK-SESSION-STABILITY-PROJECTION-FRESHNESS-PROMPT-PACK`
- Date: `2026-07-02`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `freeze the future read-only projection freshness checker contract without implementing it`
- Control-plane checkpoint: `main@28f2cab7`
- Worker implementation: `not included`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`
- Marker movement: `none`

## Objective

Freeze the implementation handoff for the first projection freshness checker so the future worker can answer:

`Are ATLAS root projections stale relative to current root truth, owner-lane semantics, receipts, manifests, marker posture, PR metadata, and proof state?`

Expected future files:

- `ops/atlas/projection_freshness.py`
- `tests/test_atlas_projection_freshness.py`

## Required CLI Flags

The future worker must support:

- `--json`
- `--strict`
- `--output <root-relative-path>`
- `--pr <owner/repo#number>` for read-only PR body/head comparison when explicitly supplied
- `--skip-pr` to avoid network or GitHub metadata checks
- `--owner-status <repo-id-or-path>` as read-only owner-lane classification input only

Default behavior:

- read-only inspection
- no writes unless `--output` is provided
- no network unless a PR check is explicitly requested
- deterministic stdout summary plus JSON when `--json` is supplied
- fail closed when required local truth cannot be read

## JSON Output Fields

The future worker must emit one object with:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `parity`
- `stack_lock`
- `inventory`
- `atlas_book`
- `receipts`
- `manifests`
- `markers`
- `pull_requests`
- `owner_lanes`
- `proof_state`
- `protected_surfaces`
- `blockers`
- `warnings`
- `required_refreshes`
- `safe_to_continue`

The schema version is `atlas.projection_freshness.v1`.

## Exit-Code Policy

Default mode:

- `0` for `ok`
- `0` for `advisory_drift`
- `2` for `blocker`
- `3` for `internal_error`

Strict mode:

- `0` for `ok`
- `1` for `advisory_drift`
- `2` for `blocker`
- `3` for `internal_error`

## Allowed Read-Only Checks

The future worker may read:

- root branch, HEAD, upstream parity, staged names, unstaged names, and untracked names
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- continuity manifests under `docs/memory/initiatives/`
- latest stack validation receipt under `runtime/receipts/validation/`
- marker selector output
- continuity health output
- PR metadata/body only when explicitly requested
- owner repo branch/status/HEAD only when explicitly requested as read-only status

## Forbidden Mutation Behavior

The future worker may not:

- mutate root projections
- mutate owner repos
- mutate Supabase, Vercel, BrowserStack, GitHub secrets, or deployment surfaces
- stage, commit, push, merge, or change branches
- edit PR bodies
- deploy or publish
- generate receipts
- move markers
- clean residue
- touch `archive/`, `.playwright-mcp/`, `.vercel/`, `secrets/`, or `.env*`
- treat dry-run proof as protected proof
- claim root readiness when validation has `critical` or `error`

## Stop Conditions

The future worker must report `blocker` when:

- root parity cannot be read
- stack lock or inventory cannot be read
- marker board and manifest truth contradict in a way that would change a readiness claim
- validation has `critical` or `error`
- protected proof is claimed but only dry-run proof is present
- owner-lane dirt is root-blocking according to inventory
- PR body references stale heads for an in-scope PR
- output path is absolute, outside the root, or protected
- an honest answer would require owner/platform mutation

## Proof Matrix

The worker implementation packet must prove:

1. clean local projections return `ok`
2. stale markdown inventory relative to JSON returns `advisory_drift` or `blocker` according to claim severity
3. stale marker mirror relative to manifest returns `advisory_drift`
4. stale PR head metadata returns `blocker` when PR scope is explicit
5. dry-run proof represented as protected proof returns `blocker`
6. advisory owner-lane dirty state does not block root
7. root-blocking dirty state blocks root
8. unsafe output paths are rejected
9. deterministic JSON ordering holds
10. strict mode maps advisory drift to exit code `1`

## Marker Decision

No marker moves from this prompt-pack.

`AI Work Session Stability & Auto-Sync Loop` remains `40%`.

## Next Packet

`AI Work Session Stability & Auto-Sync Loop projection freshness checker implementation-readiness closeout and worker-routing`

That next packet should decide whether the worker can be routed to exactly `ops/atlas/projection_freshness.py` and `tests/test_atlas_projection_freshness.py`.
