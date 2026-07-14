# DiscordOS Mazer Board Normalization Live Repair

## Decision

Accept the bounded live repair as objective evidence for the active
`DiscordOS Cross-Project Board Integrity & Lifecycle Repair` lane. Keep the
lane at `0 / 10` because this cluster repaired one admitted board class but did
not close any proof unit across the complete registered denominator.

## Scope

DiscordOS remained the sole writer. The cluster targeted the `58` drifted
active Mazer cards identified by the paginated registry scan. It did not
authorize any Fitness, Music Sesh, shared Completed, legacy, or other project
board mutation.

The migration planner proved:

- `58 / 58` exact owner thread matches;
- zero ambiguous matches;
- zero duplicate owner thread or card identities;
- zero accepted fallbacks;
- zero accepted title-only matches.

## Live result

Six guarded batches repaired `54` cards with batch sizes
`10 / 10 / 10 / 10 / 10 / 4`.

| Evidence | Result |
|---|---:|
| Starter-message readbacks | `54 / 54` |
| Journal-message readbacks | `54 / 54` |
| Stable identities repaired | `54` |
| Canonical bodies repaired | `54` |
| Updated timestamps repaired | `54` |
| Cards deleted, archived, or reopened | `0` |
| Other-board mutations | `0` |

Mazer moved from `7` healthy and `58` drifted cards to `61` healthy and `4`
drifted cards while its `65`-card active denominator stayed unchanged.

The final cross-project readback reported `283` current cards, `126` healthy,
and `157` drifted. The one-card denominator increase was a concurrently added
healthy shared Completed card outside this repair scope; the repair did not
revert it.

## Withheld cards

Four exactly mapped cards were withheld because the current migration planner
would overwrite newer journal lifecycle truth:

| Card ID | Discord thread | Journal state | Unsafe planned state |
|---|---|---|---|
| `mazer-auth-gate-persistent-login` | `1524974571059675198` | `in_progress` | `review` |
| `mazer-discordos-board-discipline` | `1524974583348858880` | `in_progress` | `review` |
| `mazer-auth-ui-flow-hardening` | `1525635672961060925` | `planning` | `in_progress` |
| `mazer-shared-run-status-panel` | `1526644909241667644` | `planning` | `in_progress` |

The remaining drift reasons are exactly:

- `stable_card_id_missing: 4`;
- `canonical_card_body_missing: 4`;
- `canonical_updated_timestamp_missing: 4`.

## Required owner fix

Normalization-only migrations must preserve existing live journal lifecycle.
A stale owner export or raw `open` baseline cannot advance or regress state.
An actual lifecycle transition remains valid only when it is explicit,
authorized, and represented by the event contract.

After that owner-side planner fix passes focused and full verification, rerun
only the four withheld stable IDs through plan, dry-run, guarded apply, exact
starter/journal readback, Mazer consistency, and the complete registry scan.

## Evidence

- Human receipt:
  `runtime/board-integrity/mazer-normalization-2026-07-14/RECEIPT.md`
- Machine receipt:
  `runtime/board-integrity/mazer-normalization-2026-07-14/RECEIPT.json`
- Final registry scan:
  `runtime/board-integrity/mazer-normalization-2026-07-14/15-registry-after.json`

No repository code was edited by the live repair. No commit, push, pull
request, production deployment, deletion, retention change, or Atlas marker
mutation occurred.
