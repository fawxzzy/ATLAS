# Cortex Event-Triggered Runtime Read-Model Refresh Proof

Date: 2026-07-17

## Outcome

Activation step 6, `cortex-event-refresh`, is accepted. One explicit accepted
activation-state event produced exactly one deterministic source-only refresh of
the principal Cortex current-state, context, and operator-surface read models.
Replaying identical inputs is a byte-stable no-op. Step 7, `DiscordOS
interaction-first reliability review`, is now the exact selector; steps 7 and 8
remain pending.

Creation OS PR #134 remains merged advisory history at `0cdfb177` and was not
reopened, rerun, or relabeled.

## Pinned authority

- ATLAS repository: `fawxzzy/ATLAS`
- source ref: `main`
- source commit: `90f9de1dd55fe17b8fd2623b71193a6cc332e8f1`
- source tree: `3ef6ec258d17d034ca8b42e6cc7214df84b2fe48`
- runtime-placement registry Git blob: `bc513e150b1acdb02928566c8e3f6b008d025f73`
- registry SHA-256: `sha256:8873d926818944c7667fc911d9a88c45d2b411da30ae14f6393f4703309387ce`
- accepted event: `cortex-event-refresh-step-6-accepted-90f9de1d`
- durable event ref:
  `runtime/cortex/events/cortex-event-refresh.step-6.accepted.v1.json`
- correlated receipt ref:
  `runtime/receipts/cortex/cortex-event-refresh.step-6.execution-receipt.v1.json`
- event SHA-256: `sha256:9819f1aba325afbe5605df156b33de5ed16f626be6236b907f981f36a1f7e4da`
- source-set SHA-256: `sha256:d567e1fe75dacddd0f415c9296518eb6912f6099824eff5a11818d56b8dff41e`

The source set binds the runtime-placement registry/schema, lane registry,
marker book, existing Cortex current-state/context/operator primitives,
canonical artifact helpers, semantic validator, architecture boundary, accepted
event, transform, and schemas. No owner checkout or mutable runtime-health
surface is an authority input.

The accepted event, six generated outputs, and correlated receipt are durable
tracked artifacts even though their `runtime/**` locations are ignored by
default. A fresh checkout therefore has the complete accepted input and output
set required for deterministic replay; this proof does not depend on ignored
worktree residue. Exact `.gitattributes` entries pin the transform, schemas,
event, outputs, and receipt to LF so raw-byte digests remain stable across
Windows and Linux checkouts.

## Trigger and rejection contract

The only admitted trigger is a schema-valid event with `event_status=accepted`
and an exact `cortex-event-refresh` transition from `pending` to `accepted`
against the first unresolved step at the pinned registry blob.

- malformed event: rejected before writes
- non-accepted event: rejected before writes
- stale source commit, tree, registry blob, hash, selector, or from-status:
  rejected before writes
- identical duplicate: no-op with zero refreshes
- duplicate-conflicting output or receipt: rejected without rewrite
- partial output set without its correlated receipt: rejected without adding
  or rewriting any output
- accepted change cardinality: exactly one step

The adapter is invoked directly for the accepted event. It has no polling loop,
daemon, scheduler, standing server, or second queue.

## Read-model before and after

| Artifact | Before generated | Before SHA-256 | After generated | After SHA-256 |
| --- | --- | --- | --- | --- |
| `runtime/cortex/current-state/latest.json` | `2026-07-06T06:22:19.476929Z` | `sha256:0daf01a2cbbeace49f73b3eb076e0e4daf3707fcff37c0c75fd3b1ef33d0a4d2` | `2026-07-17T03:32:30Z` | `sha256:3ea1990067f7c83df4923ac86dd29398bda1f2127b94e8b9353876239310eb19` |
| `runtime/cortex/current-state/latest.md` | n/a | `sha256:dfc9cf5648f3948d49085128f1d4eb8efc1c7004ffa58e3d680cc9ce8da87c97` | `2026-07-17T03:32:30Z` | `sha256:4cfe7e38018e073803aadb78d9dde76dbbcfcd3b9e3710d6532974ca22b453a5` |
| `runtime/cortex/context/latest.json` | `2026-07-06T06:22:20.080988Z` | `sha256:5048d222f5def6bffc6cd990945ad9e2e0454b59cf9ffecbeb29aa9e39270446` | `2026-07-17T03:32:30Z` | `sha256:c76fd06437e2a0afc96308b149bf36b4d866a08530944854a465127ef19e21c3` |
| `runtime/cortex/context/latest.md` | n/a | `sha256:a7b4f706ca4d5007f7dbd821a9af3c16777826b4c0f0c877f2808848d35d3403` | `2026-07-17T03:32:30Z` | `sha256:90dcc5993d42b82d841967649b399808c6cd250d42dd99c467b4d25780f4a8b3` |
| `runtime/cortex/operator-surface/latest.json` | `2026-07-06T06:22:20.443544Z` | `sha256:afeb7a2b1c70e74835e77be76e000b426750bba75572d0c6cb0511e932da5662` | `2026-07-17T03:32:30Z` | `sha256:5e20f35a5736481c8e4fc9988060654537aaf51fe04dc5d8096fbad853cd0663` |
| `runtime/cortex/operator-surface/latest.md` | n/a | `sha256:a1d74ec515d0897d96dfd3a8191ca77a97946aa34c5819fd9482f1bd6b51b36f` | `2026-07-17T03:32:30Z` | `sha256:a5d529843fd10198a3ecbc18f72de3bb4242dc5ff35700b91b7aed914601dba5` |

Output-set digest:
`sha256:3c1f4ae7493cc30264127a6a7bcee112a1e5c806a40e21f78fa5b72a2e4610a3`.

The read models preserve `UNKNOWN`, `blocked`, `stale`, and `pending` as distinct
arrays. The stale Cortex-artifact UNKNOWN is resolved by this event. Other
unavailable owner/runtime observations remain UNKNOWN and no owner health is
inferred.

## Selector and markers

- before: step 6 `pending`; selector `Cortex event-triggered runtime read-model refresh proof`
- after: step 6 `accepted`; selector `DiscordOS interaction-first reliability review`
- step 7: `pending`
- step 8: `pending`
- Runtime Activation Readiness: unchanged `8 / 8`
- Runtime Correlation Reliability: unchanged `5 / 5`
- Operator Surface Adoption: unchanged `4 / 4`
- historical snapshots: unchanged

## Verification

- focused event/read-model/replay/rejection tests: passed locally, including
  malformed, non-accepted, stale, duplicate-conflicting, and partial-set cases
- deterministic write then identical check replay: passed; second outcome `noop`
- event, three JSON read models, receipt, and runtime-placement schema
  validation: passed
- pinned source-only runtime-placement semantic validation: passed
- root QA unit tests: `78` passed
- focused Cortex/runtime-placement/current-state tests: `41` passed
- owner-export tests: `6` passed; canonical replay reported `atlas_cards=36`,
  `cortex_cards=2`, and `discord_mutation_authorized=false`
- authoritative source-only stack validation: `0` critical, `0` error, and
  `10` expected sparse-checkout warnings with the established empty ephemeral
  `repos/repo-backups` presence fixture; the fixture and its temporary parent
  were removed immediately and left no residue
- exact-base sparse validation parity: the unfixtureed base and branch both
  report the same pre-existing `1` archive-presence error and `10` sparse
  checkout warnings
- changed-surface JSON/schema scan: `11` JSON documents parsed, `3` schema
  definitions checked, `5` schema instances validated
- changed-surface machine-path and credential scan: zero hits

## Authority and prohibited actions

Cortex remains read-only and advisory. This refresh performed no owner-repo,
Discord, board, Vercel, Supabase, database, secret, scheduler, service,
production, or historical-snapshot mutation. Discord mutation authorization is
`false` in both the event and generated operator/receipt surfaces.

## Publication settlement

The ready pull request, green exact-head hosted CI, fresh exact-head Codex
review, and zero-thread settlement are post-commit control-plane gates. Their
exact refs are recorded in immutable PR metadata and the two terminal task
receipts. They are intentionally not folded back into this source-bound file:
doing so would create a new head that invalidates the exact-head CI and review
being recorded.
