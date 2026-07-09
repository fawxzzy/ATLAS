# Vercel Platform Observability Governance log and runtime-error inventory contract freeze

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root docs-only contract freeze`
- Control-plane checkpoint: `310a8fa54734962ebe62a1e2ef1d1fa8d76e2aad`
- Marker movement: none

## Decision

Freeze one bounded read-only contract for future Vercel log and runtime-error inventory across the governed project set.

The next exact packet is:

```text
Vercel Platform Observability Governance log and runtime-error inventory first-implementation admission
```

This packet does not pull live logs, stream runtime events, call mutation-capable APIs, read env values, read token values, mutate Vercel, mutate owner repos, or move the marker above `0%`.

## Why This Contract Exists

The project-inventory layer is now reconciled.

That earlier chain proved:

- governed project coverage is `5/5`
- the root-owned inventory helper remains `status=ok`
- the helper remains `safe_to_use=true`
- `missing_projects=[]`
- the governed Vercel set can be described without env-value, token-value, or mutation access

The next highest-value observability surface is therefore logs and grouped runtime errors.

That surface is materially different from project inventory because it can contain request material, customer data, auth material, payment-adjacent payloads, or secret-bearing text if handled carelessly. The boundary has to be frozen before any capture or helper implementation is admitted.

## What Inventory Coverage Already Proves

Project-inventory coverage now proves:

- the governed project set is complete for this lane
- project-level identity and deployment-adjacent metadata can be handled safely at ATLAS root
- root can hold a read-only Vercel observability lane without widening into deployment or secret authority
- the audit already demonstrated that grouped runtime-log and grouped runtime-error surfaces are visible

Project-inventory coverage does not yet prove:

- a safe log wrapper contract
- a safe grouped runtime-error inventory contract
- a redaction-safe JSON Lines intake boundary
- a build-log summary boundary
- a reusable helper for log/runtime-error aggregation

## Why Logs And Runtime Errors Are Next

The capability audit already showed that the connected Vercel surfaces expose:

- grouped runtime-log queries
- grouped runtime-error queries
- build-log tails

It also recorded one concrete grouped Fitness runtime-error family:

- label: `billing-webhook-stripe`
- route: `/api/billing/webhook/stripe`
- occurrences: `168`
- affected users: `7`
- first seen: `2026-07-01T20:54:17.000Z`
- last seen: `2026-07-09T05:34:02.000Z`
- deployment: `dpl_HUsDUbhofhJFEKxLCazcDfQk8pTM`

That makes the log/runtime-error surface the next credible read-only packet, but still only as doctrine in this receipt.

## In-Scope Projects

This contract applies only to:

- `fawxzzy-discordos`
- `fawxzzy-fitness`
- `fawxzzy-mazer`
- `fawxzzy-trove`
- `fawxzzy-foundation`

No project outside this governed set may be admitted by the future helper.

## Admitted Observability Surfaces

The future helper may inventory only these read-only surfaces:

- request logs
- runtime logs
- grouped runtime errors when the connector exposes them
- build-log summaries only when they can be treated as non-secret summary evidence

This packet admits inventory, classification, and aggregation only. It does not admit broad exploratory log spelunking.

## Excluded Surfaces

The future helper and any future packet under this contract must exclude:

- env values
- token values
- secret-bearing output
- raw customer payloads
- request bodies
- auth cookies
- authorization headers
- payment or customer data
- mutation payloads
- full raw build logs when they contain secrets or secret-adjacent output

## Allowed Filters

The future log/runtime-error inventory helper may filter only by admitted read-only selectors such as:

- project
- deployment
- environment
- level
- status code
- source
- query
- request id
- since
- until
- branch

Filters are allowed only to narrow read-only inventory scope. They do not widen authority.

## Allowed Output Shape

Durable outputs under this contract may contain only sanitized aggregate or summary fields such as:

- aggregate counts
- route or path patterns
- status-code families
- error class or message hash
- first seen
- last seen
- affected project slug
- affected deployment id
- sample count
- source type
- capture window metadata

Durable outputs may describe trends and clusters, but not retain raw secret-bearing events.

## Forbidden Output Shape

Durable outputs under this contract must not contain:

- raw token values
- raw env values
- raw request bodies
- raw headers containing cookie or authorization values
- private customer data
- payment event payloads
- unredacted message bodies that embed secrets
- full unredacted stack traces when they contain secrets, keys, or customer payloads

## Redaction Rules

Future helper behavior under this contract must be fail-closed.

Minimum redaction rules:

- drop authorization and cookie values entirely
- drop request bodies entirely
- drop query-string values when they may contain secrets or customer identifiers
- preserve route patterns, not raw personalized URLs
- preserve error grouping labels or message hashes instead of verbatim secret-bearing error strings when redaction is uncertain
- preserve deployment ids, status-code families, counts, and time windows
- reject any record that still contains obvious token, secret, cookie, bearer, or env-value material after sanitization

When uncertain whether a field is safe, the field must be excluded rather than retained.

## JSON Lines Intake Boundary

`vercel logs --json` style JSON Lines or equivalent NDJSON may be used only as transient intake under `tmp/**`.

Contract consequences:

- raw JSON Lines must never be committed by default
- any JSON Lines admitted for helper intake must stay local under `tmp/**`
- durable receipts may cite only sanitized aggregates derived from those lines
- the future helper must tolerate JSON Lines input only after path and schema checks pass

## Connector Intake Boundary

Connector-sourced grouped runtime-log or grouped runtime-error results are admitted only as sanitized summary evidence.

Connector intake may preserve:

- project slug
- deployment id
- route pattern
- aggregate counts
- affected-user count when the connector returns it as an aggregate
- first-seen and last-seen timestamps
- grouping label or normalized error family

Connector intake must not be widened into unrelated project mutation, env inspection, alias mutation, or deployment control.

## CLI Intake Boundary

CLI intake is admitted only for read-only log inspection and only through local transient artifacts under `tmp/**`.

CLI intake may include:

- `vercel logs` summary output
- `vercel logs --json` JSON Lines output
- time-bounded, filter-bounded runtime-log evidence

CLI intake must not include:

- token-bearing shell transcripts
- env dumps
- copied terminal history
- follow-mode output committed directly into the repo

## `tmp/**` Wrapper And Report Boundary

Future helper intake and local reports for this lane may live only under root-relative `tmp/**`.

Admitted placement for future local artifacts:

```text
tmp/atlas/vercel-observability/
```

Contract consequences:

- raw wrappers, JSON Lines, NDJSON, or sanitized local helper reports stay under `tmp/atlas/vercel-observability/`
- `tmp/**` artifacts are local runtime evidence, not default commit material
- only docs receipts, tests, and future helper source files are eligible for durable commit unless a later packet explicitly widens that rule
- absolute paths and parent traversal remain forbidden

## Runtime-Error Cluster Model

The future helper should treat one runtime-error cluster as a read-only observability aggregate with fields such as:

- project slug
- environment
- route pattern
- grouping label or normalized error family
- occurrence count
- affected-user count when exposed as an aggregate
- first-seen timestamp
- last-seen timestamp
- referenced deployment id

The helper should summarize clusters across admitted captures, not store raw per-user or per-request payloads.

## Fitness Error-Cluster Observation Boundary

The existing Fitness grouped runtime-error observation is admitted here only as evidence that the surface is real.

This contract allows that cluster to be recorded as:

- observability evidence
- a future helper test fixture target
- a proof point for the value of grouped runtime-error inventory

This contract does not allow that cluster to become:

- a Fitness implementation packet
- a Stripe remediation packet
- a webhook debugging packet
- a deploy or rollback packet

## Mutation And Authority Denials

This contract preserves the following denials:

- no Vercel mutation
- no deploy, redeploy, promote, rollback, alias, or domain action
- no env-value capture
- no token-value capture
- no secret capture
- no owner-repo mutation
- no DiscordOS, Fitness, Mazer, Trove, or Foundation implementation work
- no marker ratchet above `0%` from doctrine alone

## Future Implementation Boundary

The next implementation packet may admit only the first root-owned helper for this contract.

Expected future implementation files:

- `ops/atlas/vercel_log_runtime_error_inventory.py`
- `tests/test_atlas_vercel_log_runtime_error_inventory.py`

That future helper should:

- read sanitized operator, connector, or CLI log wrappers under admitted `tmp/**`
- validate schema and path safety
- reject raw secret, env, token, cookie, or body payloads
- aggregate route, error-family, status-family, and deployment counts
- preserve a read-only posture
- avoid any deploy, env, or mutation API behavior

## Marker Decision

No marker movement.

`Vercel Platform Observability Governance` remains `0%`.

Reason:

- this packet freezes doctrine only
- no log/runtime-error helper exists yet
- no first implementation is admitted yet
- no reconciled implementation proof exists yet

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance log and runtime-error inventory first-implementation admission
```

That packet may admit the first helper and focused tests, but must still keep live log capture, env-value surfaces, secret handling, Vercel mutation, and owner-repo mutation denied unless a later packet explicitly changes the contract.

## Completion

Completion: `100%` for the log and runtime-error inventory contract freeze itself.

No Vercel mutation was performed.
No owner repo was mutated.
No env values or token values were read or committed.
