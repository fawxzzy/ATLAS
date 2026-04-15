# ATLAS Awareness API Runbook

## Purpose

The Awareness API is the root-owned read boundary for ATLAS state.

It answers:

- what exists
- what is true now
- what needs attention
- what a governed session or artifact currently says
- what knowledge can be queried under indexing policy

It does not execute machine actions.

It is the single read model for ChatGPT, voice, CLI, UI, and the hosted MCP bridge.

## Ownership

- owner: stack root / Cortex-adjacent read layer
- entrypoint: `ops/atlas/serve_awareness.py`
- backing state:
  - `runtime/state/atlas/world-model.snapshot.latest.json`
  - `runtime/state/atlas/world-model.attention.latest.json`
  - `runtime/state/atlas/observations/**`
  - `runtime/cortex/artifacts/**`
  - `runtime/cortex/query/knowledge/bundle.json`
  - request audit log: `runtime/atlas/awareness/requests/*.jsonl`

## Transport Model

- transport: HTTP JSON over a read-only endpoint set
- source of truth: root world model plus governed receipts and catalogs
- rebuild rule: reads use the latest emitted world-model artifacts by default and rebuild only when `refresh=true` is requested or the cached world-model files are missing
- cache posture: digest-backed responses with `ETag`; repeated unchanged reads should stay stable
- mutation rule: no execution, no write-through, no Lifeline shortcut

The Awareness API is the externalized cognition surface. Clients query it first, then hydrate specific artifacts only when needed.

## Read Model

The API serves the current emitted world model and only rebuilds on demand. That keeps the boundary query-first and avoids turning every read into a full hydrate cycle.

Observation closure currently comes from two lanes:

- source emitters in root-owned session, knowledge, and validation flows
- Cortex sync backfill for governed historical descriptors and receipts

## Endpoints

Base URL example: `http://127.0.0.1:8765`

- `GET /health`
- `GET /atlas/status`
- `GET /atlas/inventory`
- `GET /atlas/snapshot`
- `GET /atlas/attention`
- `GET /atlas/search?q=<query>&limit=<n>`
- `GET /atlas/knowledge/query?q=<query>&limit=<n>`
- `GET /atlas/sessions/<session_id>`
- `GET /atlas/artifacts/fetch?id=<search-id>`
- `GET /atlas/artifacts/fetch?ref=<atlas-relative-path>`

## Fetch Policy

Artifact fetch is allowlisted and fail-closed.

Allowed roots:

- `docs/**`
- `ops/**`
- `runtime/atlas/sessions/**`
- `runtime/cortex/catalog/knowledge/**`
- `runtime/cortex/context/**`
- `runtime/cortex/query/knowledge/**`
- `runtime/cortex/supervisor/**`
- `runtime/lifeline/worker-execution/**`
- `runtime/receipts/**`
- `runtime/state/atlas/**`
- `stack.yaml`
- `stack.lock.yaml`
- `README-STACK.md`

Blocked by omission:

- `secrets/**`
- `tmp/**`
- raw knowledge imports under `data/imports/**`
- quarantined Verta raw material

## Auth

Loopback development can run without auth.

Remote or shared binds should always require a bearer token.

Supported inputs:

- `--auth-token <token>`
- `--auth-token-file <path>`
- `--auth-token-previous <token>`
- `--auth-token-previous-file <path>`
- `ATLAS_AWARENESS_TOKEN`
- `ATLAS_AWARENESS_TOKEN_FILE`
- `ATLAS_AWARENESS_PREVIOUS_TOKEN`
- `ATLAS_AWARENESS_PREVIOUS_TOKEN_FILE`

Header:

- `Authorization: Bearer <token>`

Fail-closed behavior:

- remote binds without a token are rejected unless `--allow-unauthenticated` is explicitly set
- invalid or missing tokens return `401`
- tokens are never written to disk; request logs store only a token fingerprint

Rotation rule:

- publish a new current token
- keep the prior token in the previous-token slot during the migration window
- remove the prior token once all clients have rotated

## Abuse and Retention Controls

Supported server knobs:

- `--request-log-retention-days`
- `--rate-limit-window-seconds`
- `--rate-limit-max-requests`
- `--deployment-profile local-only|hosted`

Behavior:

- request logs are pruned by age
- rate limiting is enforced per client address
- error payloads include a stable category and retryability signal

## Request Logging

Every request appends a JSONL audit record under `runtime/atlas/awareness/requests/`.

Logged fields include:

- timestamp
- request id
- remote address
- route
- query key shape, not raw query values
- status code
- duration
- auth result
- deployment profile
- response digest tag when available
- never raw bearer tokens or sensitive request payload bodies

## Knowledge Boundary

Knowledge reads must respect the bundle query policy.

- metadata-only archives remain metadata-only
- `personal--verta-core` and `personal--verta-core-sanitized` stay queryable only through metadata and receipt refs
- derived summaries, topic maps, and evidence refs are withheld when `derived_searchable` is false

Search must follow the same rule. Metadata-only archives must not score or preview against derived terms.

## Startup

Local loopback:

```powershell
python ops/atlas/serve_awareness.py --host 127.0.0.1 --port 8765
```

Hosted or remote bind:

```powershell
python ops/atlas/serve_awareness.py --host 0.0.0.0 --port 8765 --deployment-profile hosted --auth-token-file secrets/local/atlas-awareness.token --auth-token-previous-file secrets/local/atlas-awareness.previous.token
```

The server returns JSON only.

## Deployment Notes

- keep this service read-only
- keep it colocated with the root runtime and query bundle
- terminate TLS at the host or reverse proxy in front of this service
- do not expose raw runtime directories directly; expose only the API
- do not reuse this surface for approvals or execution

## Verification

Recommended checks:

```powershell
python ops/atlas/serve_awareness.py --host 127.0.0.1 --port 8765 --auth-token local-test
python ops/atlas/check_awareness_health.py --base-url http://127.0.0.1:8765 --auth-token local-test
python -c "import json, urllib.request; req=urllib.request.Request('http://127.0.0.1:8765/atlas/artifacts/fetch?id=knowledge:personal--verta-core', headers={'Authorization':'Bearer local-test'}); payload=json.loads(urllib.request.urlopen(req).read().decode()); print('metadata-only' if 'withheld' in payload['text'] else 'unexpected')"
python ops/validation/validate_stack.py --ratchet
```

Expected properties:

- repeated authenticated status reads return digest-backed snapshot data
- repeated identical status reads keep the same `ETag` until source state changes
- knowledge fetch for Verta returns metadata-only content
- observation store exists under `runtime/state/atlas/observations/**`
- request logs appear under `runtime/atlas/awareness/requests/**`
- ratchet stays green

## Health Endpoint

`GET /health` returns:

- service name
- deployment profile
- auth-required flag
- request-log retention days
- rate-limit configuration
- digests for registry, world model, attention, and working memory

Remote clients should use these digests to reason about staleness instead of assuming every response is freshly recomputed.

## Non-Goals

- no direct Lifeline execution
- no raw repo traversal as API contract
- no transcript-backed memory surface
