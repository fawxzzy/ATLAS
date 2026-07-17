# ATLAS Runtime Placement Read-Model, Marker, And Selector Reconciliation

Date: `2026-07-16`

Mode: bounded ATLAS-root truth reconciliation from accepted owner evidence.

Base authority: GitHub `main` at
`ebc6243501a1b9208b5fc9f2ddbdb563496adecd`, tree
`ff9a49115ffa70f6028a80715e2d541c0b80a9f8`, merged by ATLAS PR `#136`.

Branch: `codex/atlas-runtime-placement-reconciliation-20260716` in a fresh
isolated checkout. The canonical Atlas checkout and every owner repository were
read-only evidence sources.

## Result

The stale selector no longer routes the already-completed Playbook bootstrap
and foreground Observer packet. The frozen v1 `activation_sequence` remains its
original ordered string-ID array for consumer compatibility. A separate
`activation_steps` collection carries structured status and evidence, maps
one-to-one and in order to the v1 sequence, and drives the selector as the first
step whose status is not `accepted`.

Accepted steps must form a contiguous prefix. `accepted`, `pending`, `blocked`,
and `unknown` remain distinct. Prose never closes a step, and only `accepted`
marker units contribute to deterministic counts.

Selector before:
`Playbook bootstrap and foreground Observer health proof`.

Selector after:
`Cortex event-triggered runtime read-model refresh proof`.

## Accepted owner evidence

| Owner | Accepted evidence | Exact merged head | Consequence |
| --- | --- | --- | --- |
| Playbook | [PR #27](https://github.com/fawxzzy/playbook/pull/27) | `8aa912b492e689fca4c296d59a438c2813cba4fc` | build/CLI and foreground Observer health proof accepted; stable execution home clean/detached at the receipt head |
| Lifeline | [PR #35](https://github.com/fawxzzy/lifeline/pull/35) | `ca542081193b69144fdd125b8cc9b1448b67bb42` | tree-equivalent to receipt head `bca9d7b1`; build/doctor, state placement, supervision/restart, and deterministic restore proof accepted |
| `_stack` | [PR #9](https://github.com/fawxzzy/_stack/pull/9) | `7aed5495d2702a653e461549877d8fa77b3a33d2` | one bounded serialized sweep plus deterministic correlation scenarios accepted |
| ATLAS placement baseline | [PR #131](https://github.com/fawxzzy/ATLAS/pull/131) | `d1b307a95ba230c28e30f85d6570e783c6989612` | frozen placement, activation, and marker denominators retained |
| Cortex Creation OS advisory | [PR #134](https://github.com/fawxzzy/ATLAS/pull/134) | `0cdfb177` | already merged and inactive; not reopened by this packet |

Merged PR status and exact heads are the accepted owner authority. Later owner
repository heads are not substituted for these receipt heads.

## Fresh read-only runtime observations

Observed on 2026-07-16 EDT / 2026-07-17 UTC without starting, stopping,
registering, cleaning, or mutating any resource:

- Playbook Observer: no listener on `127.0.0.1:4300`; intentionally
  stopped/restorable.
- `LifelineRestoreAtLogon`: enabled, `Ready`, logon-triggered,
  `LastTaskResult=0`; action targets the root runtime home
  `runtime/lifeline/playbook-observer`.
- `AtlasStackInboxSweep`: enabled, `Ready`, `PT5M`, `LastTaskResult=0`; latest
  observed sweep `sweep-e8c3918763fd4a0f834c68551adf30aa` succeeded with zero
  pending work, lease released, and no active lease residue.
- Foundation: HTTP `200` at `2026-07-17T01:54:48Z`.
- DiscordOS runtime health: HTTP `200`, `ok=true`, `posture=operational` at
  `2026-07-17T01:54:50Z`.

These observations do not convert stopped/restorable Observer state into
running/healthy uptime proof. No fresh actual later new-logon restoration or
sustained unattended uptime was observed.

## Runtime placement truth

- No new general-purpose ATLAS server.
- Foundation remains the hosted read-only portfolio.
- DiscordOS remains the hosted writer/API across Vercel, Supabase, and bounded
  GitHub Actions polling.
- Playbook Observer remains the private loopback cockpit.
- Lifeline remains the local supervisor and current-user restore mechanism.
- `_stack` owns exactly one bounded scheduled sweep, not permanent pollers.
- Cortex remains event-triggered, root-owned, and read-only; it is not a daemon
  or scheduler.
- Product repositories remain owner lanes and are not root-operated services.

## Deterministic marker ratchet

Only fixed units cited by accepted evidence are ratcheted:

| Marker | Before | After | Basis |
| --- | --- | --- | --- |
| Runtime Activation Readiness | `null / 8`, percentage `null` | `8 / 8`, `100%` | placement contract plus accepted Playbook, Lifeline, and `_stack` owner proof |
| Runtime Correlation Reliability | `null / 5`, percentage `null` | `5 / 5`, `100%` | deterministic `_stack` success, failure, duplicate, restart, and stale-receipt scenarios |
| Operator Surface Adoption | `null / 4`, percentage `null` | `4 / 4`, `100%` | Foundation portfolio, Playbook operations, Atlas Book doctrine, and `_stack` action routing |

Unchanged marker units:

- Atlas Contracts Mesh remains `11 / 11`, `100%`.
- Atlas Full-System Re-evaluation remains `1 / 2`, `50%`.
- Marker Integrity remains `51 / 51`, `100%`.
- Historical snapshots and receipts remain immutable.

Marker status vocabulary is `accepted`, `pending`, `blocked`, or `unknown`.
Only `accepted` counts; blocked evidence is never collapsed into unknown.

## Current unknowns

- actual later new-logon restoration after the accepted deterministic Lifeline
  restore proof
- sustained unattended Observer uptime
- PostgreSQL listener ownership on ports `5432` and `5433`
- orphan browser debugger ownership
- whether any advisory resource should later be stopped, deleted, or cleaned;
  no such authority is granted here

## Advisory resource observations

- Mazer has duplicate port `4173` ownership: node listeners on `0.0.0.0` and
  `127.0.0.1`, plus separate loopback listeners on `4174` and `4191`.
- Socials OS has an all-interface bind on `0.0.0.0:8765`.
- PostgreSQL listens on all interfaces on `5432` and `5433`; ownership is
  unknown.
- Browser debugger listeners are present; ownership is unknown.
- Registered worktree inventory is large: ATLAS `9`, `_stack` `64`, Playbook
  `14`, Lifeline `3`, Foundation `1`, DiscordOS `94`, Fitness `8`, Mazer `45`,
  Socials OS `1`, FawxzzyWeb/Trove `3`, Nat1 `2`, Playbook Demo `2`.

Every observation is advisory and grants no cleanup or mutation authority.

## Selector contract

The exact frozen v1 ID order is preserved. The structured collection must have
the same eight IDs, exactly once, in the same order. The selector is derived
from the first structured step whose status is not `accepted`; it is `null`
only when all eight steps are accepted. Tests prove that accepting the currently
selected Cortex step advances the selector to the next unresolved DiscordOS
step.

## Verification outcome

- Runtime placement schema and semantic validation reports `issue_count=0`.
- Focused runtime-placement and deterministic owner-export coverage passes
  `29` tests. Coverage includes the original v1 string-ID sequence shape,
  missing/duplicate/reordered structured-step rejection, unique public packet
  selectors, retrievable relative evidence for activation steps and marker
  units, selector advancement, accepted-prefix enforcement, blocked/unknown
  distinction, fixed-unit marker derivation, and source-only portability.
- Deterministic owner-export write and replay both report source revision
  `sha256:33ce842268106ba720722bb257053bf8d28208b9cbcae87f55716a15ddebf214`,
  `36` Atlas cards, `2` Cortex cards, and
  `discord_mutation_authorized=false`.
- Generated projection hashes:
  - Atlas owner export:
    `sha256:cc3e4e66a26f8adc17cef623dfed4aa4d526e6369e3699b228cd52abfb6a0de8`
  - Cortex owner export:
    `sha256:727e983f0ec189880720fcc058f0612d2fb16296686390cef8ce4b4daa015ed6`
  - runtime-placement registry:
    `sha256:8873d926818944c7667fc911d9a88c45d2b411da30ae14f6393f4703309387ce`
  - full-system lane registry:
    `sha256:4f27f5e8174ca4401e2ef564d25ed353868d043aed8e2b8d793f1ef3718e361e`
- Authoritative source-only root validation with missing locked repositories
  explicitly allowed and owner cleanup disabled reports
  `0 critical / 0 error / 10 warning / 0 info`. The warnings are read-only Git
  hygiene probes for intentionally absent nested `_stack` and Lifeline
  checkouts in the isolated GitHub clone.
- All five changed JSON contracts/projections parse successfully.

Exact terminal head/tree, PR, CI, fresh exact-head Codex review, zero-thread
readback, final diff/scans, and root/owner invariance are recorded in the
terminal task receipt. This committed receipt does not attempt the impossible
self-reference of embedding its own final commit hash.

## Post-merge review race

ATLAS PR `#137` merged at
`eb0402d61608da797ef5b6a0d26755d746addf9e` before its fresh exact-head Codex
review thread `PRRT_kwDOSEq72s6RoodU` became visible to the merge readback. The
late P2 was valid: an absolute or parent-traversing filesystem evidence ref
could resolve outside the ATLAS root and still count as retrievable when that
host path existed.

The additive follow-up preserves remote URL and `git:` evidence while requiring
filesystem evidence to be a non-empty, normalized, root-relative POSIX path.
POSIX absolute paths, Windows drive/UNC paths, parent traversal, and paths whose
real filesystem target escapes the resolved ATLAS root are rejected before any
existence check. Local `file:` URIs are treated as filesystem evidence and
cannot bypass containment. Focused coverage includes valid in-root evidence and
a real filesystem-link escape when the host supports links.

Follow-up verification passes `36` focused runtime-placement and deterministic
owner-export tests, the canonical semantic validator reports `issue_count=0`,
deterministic owner-export replay is byte-identical, and authoritative
source-only root validation reports
`0 critical / 0 error / 10 warning / 0 info`. The warnings remain the expected
read-only `_stack` and Lifeline hygiene probes for intentionally absent locked
repositories.

This correction changes no runtime placement, activation status, selector,
marker unit, marker percentage, generated projection, owner evidence, or
historical snapshot. The exact next packet remains
`Cortex event-triggered runtime read-model refresh proof`.

## Prohibited actions preserved

This packet does not mutate Playbook, Lifeline, `_stack`, DiscordOS, Fitness,
Mazer, Socials OS, FawxzzyWeb/Trove, Vercel, Supabase, production, Discord,
secrets, external accounts, or the canonical Atlas checkout. It does not
start/stop a service, alter a scheduled task, clean a worktree, delete a
resource, deploy, self-merge, rerun completed owner packets, reopen PR `#134`,
or route closing-audit/post-preparation work early.

## Exact next packet

`Cortex event-triggered runtime read-model refresh proof`.

That packet must deterministically refresh the accepted runtime read model
without creating a daemon or scheduler. DiscordOS reliability review and
owner-export integration remain later unresolved steps.
