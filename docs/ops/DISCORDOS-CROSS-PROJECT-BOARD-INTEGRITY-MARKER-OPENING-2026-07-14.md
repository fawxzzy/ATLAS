# DiscordOS Cross-Project Board Integrity Marker Opening

## Decision

Open `DiscordOS Cross-Project Board Integrity & Lifecycle Repair` at `0%`
on a fixed denominator of ten accepted cross-project integrity proof units.

This is a new DiscordOS owner scope. It does not reopen or invalidate the
historical closeout of DiscordOS infrastructure separation, runtime/product
hardening, publication/docs reliability, or owner-lane orchestration.

## Trigger

The preserved Mazer task records current operator-observed mismatches on
2026-07-14:

- incomplete cards did not consistently show the canonical failure/X reaction
- completed cards did not consistently show the canonical success/check reaction
- cards shipped to production were not consistently moved to Completed
- a prior repair appeared to cover one project rather than all project boards

The broader accepted board contract also requires deterministic Planning and
Ready admission, stable IDs, duplicate prevention, synchronized card bodies and
work journals, consistent formatting, source-level mojibake prevention, one
logical DiscordOS writer, idempotent apply, and exact live readback.

## Fixed denominator

| Unit | Required proof |
|---|---|
| 1 | Complete cross-project board inventory, stable-ID parity, and duplicate prevention |
| 2 | Deterministic lifecycle schema and Planning-to-Ready admission across all board classes |
| 3 | Canonical failure/X reaction parity for every incomplete lifecycle state |
| 4 | Canonical success/check reaction parity for Completed and accepted archived-complete states |
| 5 | Deterministic shipped/deployed classification, movement to Completed, and removal from the active board |
| 6 | Card body, summary, scope, dependency, priority, and evidence metadata synchronization |
| 7 | Forum-thread work-journal synchronization throughout execution and closeout |
| 8 | Title/body encoding and formatting normalization, including prevention and repair of mojibake |
| 9 | Adoption consistency across every governed project, board, and card class |
| 10 | One logical writer, dry-run, idempotent apply, exact live readback, and recurring fail-closed drift scanning |

Each unit is binary. Code-only, test-only, one-project, or stale historical proof
earns zero credit. A unit passes only with current code and tests plus live
readback for every governed board class or an explicit accepted not-applicable
disposition.

## Opening posture

- completed units: `0 / 10`
- marker: `0%`
- current audit: active, read-only, cross-project
- repair writer: not started
- Discord mutation: not performed by this opening
- card deletion or recreation: not authorized
- historical cards and receipts: preserve until classified by stable identity

## Execution order

1. Inventory all governed projects, active boards, Completed boards, card
   schemas, lifecycle states, reaction policies, body formats, journal formats,
   encoding boundaries, writers, and readback surfaces.
2. Classify each proof unit as pass, partial, fail, or unknown using current
   repository and live read-only evidence.
3. Split repairs into the smallest serialized DiscordOS owner packets.
4. For each packet, run dry-run, focused tests, full owner verification, guarded
   apply, exact live readback, and a contradiction scan before ratcheting.
5. Run a final whole-board cross-project drift scan. Close only at `10 / 10`.

## Safety boundaries

- DiscordOS remains the sole logical writer.
- Mazer and Fitness product work may continue independently.
- Repairs use stable IDs and preserve active work, journals, and history.
- No card is deleted, recreated, or moved merely because its title looks wrong.
- No production deployment, database migration, secret change, or unrelated
  owner-repository mutation is authorized by this marker opening.

## 2026-07-14 current evidence checkpoint

The opening marker remains `0 / 10` (`0%`). Current accepted evidence now
includes:

- generic lifecycle-downgrade and atomic-preflight protection merged through
  DiscordOS pull request `#69`;
- section-preserving canonical-body compaction merged through DiscordOS pull
  request `#70`;
- Mazer at `65 / 65` current cards healthy;
- Fitness at `36 / 36` current cards healthy;
- global duplicate identity count restored to `0` after a source-export/live
  identity collision was detected and corrected in the same serialized repair
  cluster;
- `atlas.project-board.owner-export.v1` registered and validated in Atlas
  Contracts;
- Unicode prevention and exact readback merged through DiscordOS pull requests
  `#76` and `#77`;
- a complete post-merge scan showing `0` current/actionable text findings while
  retaining `124` immutable Discord system-history spans across `74` messages
  and all `49` superseded threads; and
- the current registry at `288` current cards, `136` healthy current cards,
  `152` structurally drifted legacy cards, and `0` duplicate identities.

See:

- `docs/ops/DISCORDOS-MAZER-AND-FITNESS-BOARD-INTEGRITY-RECOVERY-2026-07-14.md`;
- `docs/ops/ATLAS-PROJECT-BOARD-OWNER-EXPORT-CONTRACT-V1-2026-07-14.md`; and
- `docs/ops/DISCORDOS-TEXT-INTEGRITY-RECONNAISSANCE-2026-07-14.md`;
- `docs/ops/DISCORDOS-IMMUTABLE-SYSTEM-HISTORY-RECONCILIATION-2026-07-14.md`.

No unit moves because seven required board classes remain unadmitted and the
reaction, movement, full lifecycle, formatting, and recurring drift-proof
requirements are not yet closed across the full denominator. The superseded
all-surface text gap is closed for the five enabled boards but cannot ratchet
unit 8 until all required board classes are admitted.
