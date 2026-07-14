# Owner-Lane Agent Service Bus And DiscordOS Ops Card/Board Correlation Partial Implementation And Live Readback Blocker

- Date: `2026-07-14`
- Lane: `ATLAS-root owner-lane orchestration governance`
- Mode: `bounded root-owned CardRecord/BoardEvent correlation implementation plus read-only DiscordOS blocker proof`
- Scope: `validate and correlate card/board intent while preserving DiscordOS single-writer authority`
- Control-plane checkpoint: `main@01ddf34d`
- Marker movement: `none; Owner-Lane Agent Service Bus & DiscordOS Ops Readiness remains 70%`

## Root Implementation

`ops/atlas/native_board_correlation.mjs` now:

- validates `atlas.job-envelope.v2`, `atlas.execution-receipt.v2`, and `atlas.card-record.v2` inputs;
- requires matching job, project, and card identity;
- requires a succeeded execution receipt;
- rejects stale board versions and lifecycle drift;
- emits schema-valid `atlas.board-event.v2` intent/readback artifacts;
- uses stable idempotency identity across intent and readback;
- requires observed version, readback time, and receipt reference for observed results;
- requires an error code for failed or conflicting readback;
- records `writer_authority: discordos` and cannot write Discord, Supabase, or another external system;
- writes only below `runtime/atlas/native-board-correlations/` or `tmp/`.

Focused tests: `10 / 10` passed.

The no-send canary emitted:

- event `abe_ce513691e0d3de140d223821ea0d38b1`;
- idempotency key `abk_3e16db7a1f6dddb1af1606f70303e995`;
- result `pending`;
- external mutation `not_performed`;
- writer authority `discordos`;
- independent `atlas.board-event.v2` validation `VALID`;
- exact duplicate replay produced the same event and idempotency identities.

## Live Readback Blockers

Two read-only DiscordOS commands were attempted. Neither mutated Discord, Supabase, a repository, or an artifact.

1. `ops:discordos:product-workflow-live-readback:json -- --live`
   - blocked before RPC by `missing_service_role_key`;
   - no live RPC attempt occurred.
2. `ops:discordos:mazer-feedback-board-live-readback:json`
   - reached all `40 / 40` configured active card messages with Discord HTTP `200`;
   - the validator reported `0 / 40` ready because it expects every required section in the first message;
   - the current board format uses a multi-message card journal, so the validator reports `live_message_required_markers_missing` and occasional `live_message_content_limit_exceeded` against otherwise reachable threads.

This is a readback-format compatibility blocker. HTTP reachability is not accepted as complete CardRecord/BoardEvent readback proof.

## Marker Decision

Unit 8 remains incomplete. Root intent correlation and idempotency are implemented, but the fixed denominator requires one DiscordOS-owned readback path that understands the current multi-message card format and returns a correlated applied/verified/duplicate result receipt.

Marker remains `7 / 10 = 70%`.

## Routed Blocker

`DiscordOS current multi-message board readback compatibility and service-role env blocker conversion`

Owner-side acceptance requires:

- one canonical readback command for the current journal format;
- exact card/thread/message correlation;
- idempotency-key correlation;
- observed board version or an explicit compatible version source;
- live readback receipt;
- no duplicate board writer;
- separately restored service-role environment when the Supabase readback path is retained.

## Independent Next Work

Unit 9, MarkerEvidence and KnowledgeCandidate closeout, is root-owned and does not require DiscordOS mutation. It may proceed while the unit-8 owner-side blocker remains open.

## Reusable Governance

**RULE - HTTP 200 is reachability evidence, not board-state verification.**

**PATTERN - Root intent plus owner readback.**

Atlas owns deterministic intent and correlation; DiscordOS owns mutation and live verification.

**FAILURE MODE - A readback validator assumes a single-message card after the board evolved to a multi-message journal.**
