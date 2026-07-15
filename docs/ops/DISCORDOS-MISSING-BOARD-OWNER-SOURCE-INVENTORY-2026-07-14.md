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
| Atlas | `docs/atlas-book/02-lanes-and-markers.md` and `docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json` | 33 provisional: 7 marker parents, 10 direct lanes, 16 unsplit governance records | Partial; root export required | `DUPLICATE_PARENT_CHILD`, `STALE_STATUS_CONFLICT`, `MISSING_PRIORITY` |
| DiscordOS | No accepted owner-repo work export; five Atlas-attributed candidates exist outside the owner repo | 0 owner records; 5 Atlas candidates | Blocked | `NO_OWNER_WORK_EXPORT`, `OWNER_CHECKOUT_STALE`, `ATLAS_ONLY_CANDIDATES` |
| Foundation | `repos/foundation/docs/roadmap/FOUNDATION_ROADMAP.md` | 5 explicit active Next items and 1 Atlas candidate | Partial; owner export required | `UNKEYED_MARKDOWN`, `MIXED_LIFECYCLE_PROSE`, `ROOT_CANDIDATE_UNADMITTED` |
| Lifeline | `repos/lifeline/.playbook/plan.json` and owner README | 1 underspecified next milestone; machine plan has 0 tasks | Blocked | `EMPTY_MACHINE_PLAN`, `UNKEYED_NEXT_MILESTONE`, `STALE_ROOT_INITIATIVE_CONFLICT` |
| Cortex | Root subsystem registry and Atlas planning sources | 2 candidates | Partial; root-owned subsystem export required | `ROOT_OWNED_SUBSYSTEM`, `MANIFEST_STATUS_CONFLICT`, `HELD_NO_IMMEDIATE_PACKET` |
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

Atlas root owns both exports. The Atlas export must reconcile the marker table
with the machine-readable full-system registry before assigning priorities or
card identities. Cortex remains a root-owned subsystem; an unresolved remote
repository is not owner authority.

### DiscordOS

The board writer role does not imply a project work queue. DiscordOS needs its
own owner export before Atlas-attributed infrastructure candidates can be
admitted. Current local owner-branch staleness must be resolved or explicitly
versioned in the export receipt.

### Foundation and Lifeline

Markdown Next sections are planning evidence, not deterministic card records.
Foundation must key its five active items. Lifeline must populate or supersede
its empty machine plan before the one prose milestone can become a card.

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
2. Implement the Atlas/Cortex root-owned aggregation adapter; retain the merged
   Playbook canonical-owner-JSON adapter as the second proof class.
3. Implement Foundation, Lifeline, `_stack`, and DiscordOS adapters only after
   their owner-source blockers are resolved.
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
