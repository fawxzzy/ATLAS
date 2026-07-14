# Atlas Project-Board Owner Export Contract v1

Date: 2026-07-14

## Outcome

Atlas now owns `atlas.project-board.owner-export.v1`, a backend-neutral envelope
for converting owner-repository plans into deterministic project-board input.
This is the contract foundation for admitting the seven boards that do not yet
have complete owner exports. It does not mutate Discord and does not count as
owner-adapter adoption.

## Boundary

- Owner repositories remain authoritative for project work and planning truth.
- Atlas owns the export contract, validation semantics, and admission policy.
- DiscordOS remains the only logical board writer and consumes admitted intent
  only after an owner adapter and live readback proof exist.
- `atlas.card-record.v2` remains the embedded card identity and lifecycle shape.
- This v1 seam is outside the fixed eleven-family Atlas Contracts v2 denominator.

## Contract

Each export includes:

- stable export, project, board, owner, adapter, and source-revision identity;
- one or more repository-relative source records;
- zero or more cards with stable card and idempotency identities;
- an exact embedded `atlas.card-record.v2` shape;
- source provenance and freshness state;
- summary, objective, acceptance criteria, discoveries, next actions, blockers,
  and evidence;
- parent, duplicate, and supersession relationships.

Semantic validation rejects:

- duplicate source, card, or idempotency identities;
- absolute, traversal-based, or machine-specific source paths;
- project, board, or source-reference mismatches;
- self-dependencies and duplicate dependencies;
- duplicate or superseded records without the required relationship;
- `ready` cards without an objective and acceptance criteria or with blockers;
- in-progress, review, or completed cards without objective and acceptance proof.

## Verification

- `npm --prefix packages/atlas-contracts run validate`: passed.
- Root stack validation: critical `0`, error `0`.
- Existing path warnings remain separate historical findings; the new fixture is
  repository-relative and does not add an absolute-path warning.

## Next Adapters

1. Atlas and Cortex root-owned planning sources.
2. Playbook canonical roadmap JSON.
3. Foundation, Lifeline, DiscordOS, and `_stack` after each source is made
   deterministic enough to export without inventing status or priority.

No adapter is implemented by this receipt. No Discord board or percent marker
moves until producer output, admission, application, and exact live readback are
proved for the relevant board class.
