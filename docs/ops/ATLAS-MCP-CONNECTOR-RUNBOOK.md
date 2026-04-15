# ATLAS MCP Connector Runbook

## Purpose

`ops/atlas/mcp_server.py` is the thin read-only MCP bridge over the Awareness API contract.

Current posture:

- read-only first
- fail-closed
- no Lifeline mutation tools
- designed for search/fetch style ATLAS access
- backed by the same Awareness API used by other clients

## Transport Model

The bridge supports two transports:

- stdio JSON-RPC for local development and direct connector testing
- hosted HTTP JSON-RPC on `/mcp` for remote MCP rollout

The bridge never reads ATLAS state directly when serving tools. It calls the Awareness API and inherits its query and fetch policy.

Hosted health also exposes:

- `tool_names`
- `toolset_digest`
- `registry_digest`

## Tools

The bridge exposes these tools:

- `search`
- `fetch`
- `atlas_status`
- `atlas_session_fetch`
- `atlas_query_knowledge`

`search` and `fetch` follow the OpenAI company-knowledge compatibility shape for MCP-backed data apps:

- `search` returns `{"results":[...]}`
- `fetch` returns one document object with `id`, `title`, `text`, `url`, and optional `metadata`

These tool names are registry-backed in `docs/registry/ATLAS-TOOL-REGISTRY.json`. Keep the exposed set minimal.

## Startup Modes

### STDIO MCP server

```powershell
python ops/atlas/mcp_server.py --awareness-url http://127.0.0.1:8765 --awareness-auth-token local-test
```

This mode speaks JSON-RPC over stdin/stdout and supports:

- `initialize`
- `ping`
- `tools/list`
- `tools/call`

### Local tool smoke checks

```powershell
python ops/atlas/mcp_server.py --awareness-url http://127.0.0.1:8765 --awareness-auth-token local-test --call-tool atlas_status
python ops/atlas/mcp_server.py --awareness-url http://127.0.0.1:8765 --awareness-auth-token local-test --call-tool search --args-json "{\"query\":\"verta trust gate\",\"limit\":5}"
```

### Hosted HTTP MCP bridge

```powershell
python ops/atlas/mcp_server.py --serve-http --host 0.0.0.0 --port 8766 --awareness-url http://127.0.0.1:8765 --awareness-auth-token-file secrets/local/atlas-awareness.token --server-auth-token-file secrets/local/atlas-mcp.token
```

Health check:

```powershell
python -c "import json, urllib.request; req=urllib.request.Request('http://127.0.0.1:8766/health', headers={'Authorization':'Bearer mcp-test'}); print(json.loads(urllib.request.urlopen(req).read().decode())['toolset_digest'])"
```

## Tool Intent

- `search`: find inventory, attention, session, and knowledge items
- `fetch`: retrieve a full document for a prior search result id
- `atlas_status`: return current snapshot and attention digests plus active session summary
- `atlas_session_fetch`: return manifest, descriptor, related observations, and session-local status snapshot
- `atlas_query_knowledge`: query the governed knowledge bundle directly

## Auth

The hosted bridge has two independent auth boundaries:

- inbound connector auth for `/mcp`
- outbound Awareness API auth for bridge-to-awareness calls

Supported outbound inputs:

- `--awareness-auth-token`
- `--awareness-auth-token-file`
- `ATLAS_AWARENESS_TOKEN`
- `ATLAS_AWARENESS_TOKEN_FILE`

Supported inbound inputs:

- `--server-auth-token`
- `--server-auth-token-file`
- `ATLAS_MCP_TOKEN`
- `ATLAS_MCP_TOKEN_FILE`

Header for hosted mode:

- `Authorization: Bearer <token>`

Remote binds should require auth. Loopback-only development can stay unauthenticated, but that is not the deployment posture.

## Request Logging

Hosted HTTP mode appends JSONL request logs under `runtime/atlas/mcp/requests/`.

Logged fields include:

- timestamp
- request id
- route
- rpc method
- tool name when present
- status code
- duration
- auth result
- awareness base URL
- toolset digest
- registry digest

## Trust Boundary

The MCP bridge inherits Awareness API fetch restrictions.

Important consequences:

- Verta remains metadata-only
- raw imports are not fetchable
- `secrets/**` are not fetchable
- execution artifacts may be read, but not executed
- knowledge search and fetch obey metadata-only vs derived-searchable policy from the Awareness API

If a user wants an action, the connector must route that as a separate governed request artifact and approval-backed Lifeline flow. This bridge does not provide a machine-mutation shortcut.

## ChatGPT App Posture

For ChatGPT app integration, keep the first published connector read-only.

Recommended rollout:

1. expose `search` and `fetch`
2. keep `atlas_status`, `atlas_session_fetch`, and `atlas_query_knowledge` allowlisted for operator/developer use
3. add action tools only after explicit approval and receipt rules are published

Do not add direct execution tools to this bridge before the approval loop and receipt contract are independently exposed and audited.

## Verification

Minimum verification:

```powershell
python ops/atlas/mcp_server.py --awareness-url http://127.0.0.1:8765 --awareness-auth-token local-test --call-tool atlas_status
python ops/atlas/mcp_server.py --awareness-url http://127.0.0.1:8765 --awareness-auth-token local-test --call-tool search --args-json "{\"query\":\"resume ready\",\"limit\":5}"
python ops/atlas/mcp_server.py --awareness-url http://127.0.0.1:8765 --awareness-auth-token local-test --call-tool fetch --args-json "{\"id\":\"knowledge:personal--verta-core\"}"
python -c "import json, urllib.request; req=urllib.request.Request('http://127.0.0.1:8766/health', headers={'Authorization':'Bearer mcp-test'}); payload=json.loads(urllib.request.urlopen(req).read().decode()); print(payload['registry_digest'])"
python ops/validation/validate_stack.py --ratchet
```

Expected behavior:

- tool list is stable
- hosted health reports the same registry-backed tool allowlist every time until the registry changes
- search returns real ATLAS artifacts or attention items
- fetch returns governed text, not raw quarantined content
- hosted HTTP mode logs requests under `runtime/atlas/mcp/requests/**`
- ratchet remains green
