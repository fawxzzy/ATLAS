# ATLAS Remote Deployment Runbook

## Purpose

This runbook hardens the hosted Awareness API and MCP bridge for real remote clients while keeping ATLAS read-only first.

## Deployment Profiles

### Local-only

Use loopback bind for local clients:

- Awareness: `127.0.0.1:8765`
- MCP bridge: `127.0.0.1:8766`

This is the default development posture.

### Hosted

Use explicit remote binds only with auth enabled and request logging retained:

- Awareness: `--deployment-profile hosted`
- bearer token required
- reverse proxy or host TLS termination required

## Awareness Service

Entrypoint:

- `ops/atlas/serve_awareness.py`

Hosted command example:

```powershell
python .\ops\atlas\serve_awareness.py --host 0.0.0.0 --port 8765 --deployment-profile hosted --auth-token-file secrets/local/atlas-awareness.token --auth-token-previous-file secrets/local/atlas-awareness.previous.token
```

Hardening knobs:

- token rotation via current and previous token inputs
- request-log retention pruning
- per-client request rate limiting
- digest-backed `/health`
- stable `ETag` on unchanged `/atlas/status`

## MCP Bridge

Entrypoint:

- `ops/atlas/mcp_server.py`

Hosted command example:

```powershell
python .\ops\atlas\mcp_server.py --serve-http --host 0.0.0.0 --port 8766 --awareness-url http://127.0.0.1:8765 --awareness-auth-token-file secrets/local/atlas-awareness.token --server-auth-token-file secrets/local/atlas-mcp.token
```

## Rotation Policy

Token rotation uses a simple overlap window:

1. publish the new current token
2. keep the old token in the `previous` slot
3. update clients
4. remove the old token after the migration window closes

Request logs store only a fingerprint, not the raw token.

## Audit Retention

Current request logs:

- Awareness: `runtime/atlas/awareness/requests/*.jsonl`
- MCP: `runtime/atlas/mcp/requests/*.jsonl`

Retention rule:

- keep enough history for operator review and abuse triage
- prune older request logs automatically
- never store sensitive request payload bodies in these logs

## Digests and Staleness

Hosted clients should treat these as first-class freshness signals:

- `registry_digest`
- `world_model_digest`
- `attention_digest`
- `working_memory_digest`
- MCP `toolset_digest`

Client rule:

- if the digest is unchanged, reuse cached interpretation
- if it changes, refetch the narrow artifact or search results you need

## Abuse Controls

- rate limit per remote client address
- keep the MCP tool allowlist fixed
- do not expose Lifeline mutation tools
- keep Verta metadata-only posture intact

## Health Checks

Awareness probe:

```powershell
python .\ops\atlas\check_awareness_health.py --base-url http://127.0.0.1:8765 --auth-token local-test
```

MCP health:

```powershell
python -c "import json, urllib.request; req=urllib.request.Request('http://127.0.0.1:8766/health', headers={'Authorization':'Bearer mcp-test'}); print(json.loads(urllib.request.urlopen(req).read().decode())['toolset_digest'])"
```

## Non-Goals

- no hosted write/apply surface in this lane
- no hidden remote execution bypass
- no second state model outside the Awareness API and governed runtime artifacts

