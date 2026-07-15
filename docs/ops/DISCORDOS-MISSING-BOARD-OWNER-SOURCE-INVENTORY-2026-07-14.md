# DiscordOS Missing-Board Owner Source Inventory

## Decision

Freeze the repository-supported work sources for the seven project boards that
remain unadmitted. This is an input to owner export contracts, not permission
to create forums or seed cards.

Every future seed record must come from a stable owner export with an explicit
card identity, lifecycle state, priority, source reference, and acceptance
criteria. Atlas and DiscordOS must not convert roadmap prose into live cards by
guessing.

## Owner-source matrix

| Project | Current source evidence | Candidate records | Admission state | Blocking reason codes |
| --- | --- | ---: | --- | --- |
| Atlas | `docs/registry/project-board-owner-exports/atlas.project-board.owner-export.v1.json`, projected deterministically from the Atlas Book and full-system registry | 33 contract-valid records: 7 non-executable marker parents, 10 direct lanes, 16 root-governance backlog records | Owner export implemented; DiscordOS admission and seeding remain pending | `BOARD_UNADMITTED`, `DISCORD_FORUM_MISSING`, `SEED_NOT_EXECUTED` |
| DiscordOS | No accepted owner-repo work export; five Atlas-attributed candidates exist outside the owner repo | 0 owner records; 5 Atlas candidates | Blocked | `NO_OWNER_WORK_EXPORT`, `OWNER_CHECKOUT_STALE`, `ATLAS_ONLY_CANDIDATES` |
| Foundation | `repos/foundation/exports/foundation.project-board.owner-export.v1.json`, projected deterministically from `repos/foundation/docs/roadmap/FOUNDATION_ROADMAP.json` | 6 contract-valid non-complete records: 3 planned and 3 planned-later | Owner export implemented; DiscordOS admission and seeding remain pending | `BOARD_UNADMITTED`, `DISCORD_FORUM_MISSING`, `SEED_NOT_EXECUTED` |
| Lifeline | `repos/lifeline/exports/lifeline.project-board.owner-export.v1.json`, projected deterministically from `repos/lifeline/docs/roadmap/LIFELINE_ROADMAP.json` | 2 contract-valid intake candidates; 8 completed capabilities excluded | Owner export implemented on the currently pinned owner branch; DiscordOS admission and seeding remain pending | `BOARD_UNADMITTED`, `DISCORD_FORUM_MISSING`, `SEED_NOT_EXECUTED` |
| Cortex | `docs/registry/project-board-owner-exports/cortex.project-board.owner-export.v1.json`, projected deterministically from the root subsystem registry and Atlas planning source | 2 contract-valid root-owned subsystem records | Owner export implemented; DiscordOS admission and seeding remain pending | `BOARD_UNADMITTED`, `DISCORD_FORUM_MISSING`, `SEED_NOT_EXECUTED` |
| `_stack` | `repos/_stack/queue/README.md` plus Atlas candidates | 0 owner queue records; 5 Atlas candidates | Blocked | `READY_EMPTY_OWNER_QUEUE`, `ATLAS_CANDIDATES_UNADMITTED` |
| Playbook | `repos/playbook/exports/playbook.project-board.owner-export.v1.json`, projected deterministically from `repos/playbook/docs/roadmap/ROADMAP.json` | 35 non-complete features: 11 in progress, 8 planned, 6 planned later, 6 dependency blocked, 3 directional, 1 architecture-defined | Owner export merged and contract-valid; DiscordOS admission and seeding remain pending | `BOARD_UNADMITTED`, `DISCORD_FORUM_MISSING`, `SEED_NOT_EXECUTED` |

## Export contract required before forum seeding

Each owner must produce deterministic records containing:

- stable project-scoped card ID;
- owner project and source repository;
- exact source path and source record ID;
- canonical title and type;
- lifecycle state using the shared board lifecycle;
- priority with an explicit unknown value when genuinely unresolved;
- summary and objective;
- acceptance criteria;
- dependencies and blockers;
- next actions;
- source revision and generated timestamp; and
- an idempotency key for DiscordOS admission.

The export must distinguish parent markers, executable child outcomes,
directional ideas, dependency-blocked work, stale records, and duplicate or
superseded records. Parent and child records cannot both become executable live
cards unless the parent is explicitly modeled as an epic.

## Project-specific decisions

### Atlas and Cortex

Atlas root owns both exports. The deterministic adapter now reconciles the
marker table with the machine-readable full-system registry before assigning
card identities. The accepted GitHub `8 / 8 = 100%` closeout is synchronized
into the registry, unknown priorities remain explicit `null`, and parent
markers remain non-executable. Cortex remains a root-owned subsystem; an
unresolved remote repository is not owner authority.

### DiscordOS

The board writer role does not imply a project work queue. DiscordOS needs its
own owner export before Atlas-attributed infrastructure candidates can be
admitted. Current local owner-branch staleness must be resolved or explicitly
versioned in the export receipt.

### Foundation and Lifeline

Foundation now owns a keyed machine roadmap and deterministic export at commit
`e0c2978e4f0d0b73aaee6fc5d14b982b78d89b97`. Its adapter excludes 11 completed
records and emits exactly 6 non-complete records with stable `FDN-*` identities,
explicit `null` priority, acceptance criteria, dependencies, source revision,
and Discord mutation disabled. The export passed six focused tests, Foundation
build and local verification, Atlas Contracts validation, and remote parity.
This closes only Foundation's owner-export prerequisite.

Lifeline now owns a keyed machine roadmap and deterministic export at commit
`54eeb56006099235723b60ce44de8a65e4c85889`. The owner reconciliation classifies
`.playbook/plan.json` as verification-plan output rather than product-roadmap
authority, excludes 8 completed capabilities, and exports exactly 2 intake
candidates. Those candidates require measured evidence before implementation
and do not authorize hosted-platform growth. The export passed six focused
tests, full Lifeline verification, Atlas Contracts validation, and branch
remote parity.

### `_stack`

An empty Ready queue is meaningful. Atlas candidates remain proposals until
`_stack` accepts them into an owner queue or export. No Atlas root fallback
card creation is allowed.

### Playbook

`docs/roadmap/ROADMAP.json` remains the canonical owner source. Playbook pull
request `#24` merged the deterministic owner adapter and canonical export at
merge commit `8796b33562a2d3e20f8c494fe72e601f3b5d84b9`. The export:

- uses `atlas.project-board.owner-export.v1`;
- contains exactly 35 non-complete roadmap records;
- preserves roadmap feature IDs as card IDs;
- records unknown priority as explicit `null` without inventing ordering;
- normalizes roadmap source bytes to UTF-8/LF before hashing so Windows and CI
  produce the same source revision;
- identifies source revision
  `sha256:2945d53cbf0b80d22ddfeeaa18e0512e70802c627a4e2f79d96dd45cd08834b6`;
  and
- passed focused tests, Atlas Contracts validation, Playbook CI, and the hosted
  security program before merge.

This closes the Playbook owner-export implementation prerequisite only. It does
not create the Discord forum, enable the registry entry, seed cards, or provide
live readback.

## Admission sequence

1. Retain the implemented shared owner-export schema and validator in Atlas
   Contracts.
2. Retain the implemented Atlas/Cortex root-owned aggregation adapter and the
   merged Playbook canonical-owner-JSON adapter as two accepted proof classes.
3. Retain the implemented Foundation and Lifeline machine-roadmap adapters and
   implement `_stack` and DiscordOS adapters only after their owner-source
   blockers are resolved.
4. Validate every export without Discord mutation.
5. Create the seven empty forums through the DiscordOS single writer and read
   back exact channel identity.
6. Enable each registry entry only after its forum and source adapter both
   pass.
7. Seed cards in separately admitted, idempotent batches with exact readback.

## Boundaries

This inventory does not create forums, create cards, move cards, assign missing
priority, reinterpret roadmap status, mutate owner repositories, or advance the
DiscordOS Cross-Project Board Integrity & Lifecycle Repair marker.

Supporting owner-export readiness is now `5 / 7` (`71.4%`): Atlas, Cortex,
Playbook, Foundation, and Lifeline are contract-valid. This is not the official board
integrity marker and does not move its fixed `0 / 10` denominator.
