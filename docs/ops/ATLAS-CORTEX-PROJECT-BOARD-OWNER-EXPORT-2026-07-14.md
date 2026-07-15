# Atlas And Cortex Project-Board Owner Export

## Decision

Atlas root now owns deterministic `atlas.project-board.owner-export.v1`
adapters for the Atlas coordination board and the root-owned Cortex subsystem
board. The adapter performs no Discord mutation and does not admit either
forum by itself.

The Atlas source inventory's provisional count is now deterministic:

- `16` Atlas-board top-level registry lanes after dedicated Cortex routing;
- `6` of those lanes are non-executable marker parents for selected child
  outcomes;
- `10` are direct top-level lanes; and
- `15` backlog records are root-governance records selected by an explicit
  owner allowlist.

The resulting Atlas export contains `31` records. The Cortex export contains
the two root-owned subsystem records `lane-cortex-context-synthesis` and
`lane-cortex-boundary-decision`. Those two stable card identities are excluded
from the Atlas coordination export so every card has one authoritative board.

## Source Reconciliation

The adapter reads both:

- `docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json`; and
- `docs/atlas-book/02-lanes-and-markers.md`.

It fails closed when the accepted GitHub `8 / 8 = 100%` Book marker conflicts
with the machine registry. The registry now carries that verified closeout and
retains the daily GitHub watch as volatile health rather than reopening the
completed implementation marker.

Owner-repository implementation records and dedicated Cortex projections remain excluded from the Atlas
governance backlog selection. Playbook, `_stack`, DiscordOS, Fitness, Mazer,
Foundation, and other owners must publish or accept work through their own
adapters. Cortex remains root-owned, but its records route only to the Cortex
board rather than being duplicated onto the Atlas board.

## Determinism And Safety

- Source bytes normalize to UTF-8 with LF line endings before hashing.
- Card IDs preserve registry lane IDs.
- Unknown priority remains explicit `null`.
- Parent marker records remain non-executable.
- Child records preserve `parent_lane_id` as card relationship metadata.
- Completed source records remain completed rather than reopening as work.
- The adapter creates no forums, cards, messages, reactions, or board writes.

Canonical outputs:

- `docs/registry/project-board-owner-exports/atlas.project-board.owner-export.v1.json`
- `docs/registry/project-board-owner-exports/cortex.project-board.owner-export.v1.json`

Generate:

```powershell
python ops/atlas/project_board_owner_export.py
```

Check committed output:

```powershell
python ops/atlas/project_board_owner_export.py --check
```

Validate each output through Atlas Contracts before DiscordOS admission.

## Remaining Boundary

This closes only the Atlas/Cortex owner-export prerequisite. DiscordOS forum
creation, registry enablement, idempotent card seeding, exact live readback,
and denominator-wide board-integrity proof remain separately authorized work.
