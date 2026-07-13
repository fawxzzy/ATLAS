# GitHub Control-Plane Event Projection Contract Implementation - 2026-07-13

## Result

Atlas Contracts now defines the canonical backend-neutral GitHub projection seam:

```text
_stack normalized GitHub facts
-> atlas.github.event-receipt.v1
-> Atlas admission and deduplication
-> atlas.github.event-admission.v1
-> formatting-free atlas.github.projection-intent.v1
-> DiscordOS single writer
```

The implementation adds package schemas, fixtures, validator coverage, constants, and export-map entries. No queue, ledger backend, webhook, monitor, Discord writer, or external mutation was implemented.

## Ownership Boundary

- `_stack` remains the immutable GitHub fact producer and does not call Discord.
- Atlas owns admission, deduplication, durable correlation, ledger meaning, and projection intent production.
- DiscordOS remains the sole external writer for board/update/alert application and readback.
- `external_mutation` remains denied in all three contracts until a separately authorized consumer action exists.

## Identity And State Semantics

- Source events preserve deterministic `ghr_` event identities and `ghk_` idempotency identities.
- Atlas admission introduces deterministic `gha_` and `ghak_` identities without weakening the source-event chain.
- Projection intents introduce deterministic `ghp_` and `ghpk_` identities for formatting-free downstream application.
- GitHub fact states remain: `observed`, `empty`, `unknown`, `access_denied`, `disabled`, `conflicting`, and `not_applicable`.
- Admission decisions remain: `accepted`, `duplicate`, `rejected`, and `quarantined`.
- Projection decisions remain: `admitted`, `suppressed`, `requires_review`, and `blocked`.

## Planned Migrations

1. `_stack` later replaces its repo-local GitHub receipt schema authority with `atlas.github.event-receipt.v1`.
2. Atlas later emits accepted `atlas.github.event-admission.v1` records and correlated `atlas.github.projection-intent.v1` records into its chosen durable ledger implementation without baking backend choice into the contract.
3. DiscordOS later consumes projection intents, applies authorized board/update/alert mutations, and returns board-event/publication/readback proof without owning upstream fact semantics.

## Marker Posture

- `lane-github-control-plane-integration` evidence is widened by this contract implementation only.
- The lane percentage remains `null`.
- `Atlas Full-System Re-evaluation` remains `50%`.

## Boundaries

- No `_stack`, DiscordOS, Mazer, Fitness, Playbook, or other owner repository was edited.
- No Discord message, card mutation, workflow rerun, release action, cleanup action, deployment, or secret mutation occurred.
