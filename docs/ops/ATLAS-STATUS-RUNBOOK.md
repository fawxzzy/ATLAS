# ATLAS Status Runbook

The ATLAS status view is rendered from artifact descriptors only.

## Contract

- status reads `runtime/cortex/artifacts/**`
- status reads the governed registry snapshot from `docs/registry/`
- status does not inspect raw session logs
- status does not infer worker completion from terminal output

## Questions Answered

The current status read model answers:

- what session is active
- what descriptors exist
- which governed tool and extension surfaces are registered
- which workers are blocked or paused
- which merge requests are still open
- which receipts closed the selected session
- which quarantined trust surfaces remain metadata-only or untrusted
- which current anomalies require operator review before more work is launched

## Command

Render the global view:

```powershell
python .\ops\cortex\render_status.py
```

Render one session:

```powershell
python .\ops\cortex\render_status.py --session-id <session_id>
```

Build the world-model artifacts first:

```powershell
python .\ops\cortex\build_world_model.py
```

## Governed Surface View

The status renderer exposes governed surface identity from descriptors only:

- session manifests declare the session's governed surfaces
- worker descriptors expose `tool_id`, optional `extension_id`, and `registry_digest`
- receipt descriptors expose the same governed identity for the closing execution step
- the top-level registry section reports the current registry digest and entry counts

## Attention Queue

The status payload also emits an `attention_queue` read model.

This is a derived operator surface, not an execution queue.

Current attention items may include:

- registry load failure
- registry drift between the active session and the current registry bundle
- historical sessions in `legacy_pre_registry` compatibility mode
- unknown governed tool or extension ids referenced by active artifacts
- blocked or paused workers
- open merge requests
- failed or missing closure receipts
- active sessions waiting in `resume_ready`
- untrusted knowledge surfaces that remain quarantined

The queue must stay descriptor-backed and deterministic. It must not inspect transcripts, terminal output, or raw imported evidence.

## Epoch Compatibility

Governed runtime history is epoch-aware.

The registry-backed governed epoch starts at **2026-04-14T08:06:53Z**.

Status behavior by epoch:

- `governed_v1` surfaces missing `tool_id`, `registry_digest`, observation-chain, or closure evidence as blocking governance defects
- `legacy_pre_registry` surfaces those same gaps as compatibility attention instead of pretending the old artifact was minted under the new contract

Current status output exposes legacy compatibility through:

- `legacy_compatibility`
- `attention_queue.items[*].kind = legacy_governed_compatibility`

That keeps historical sessions queryable without lying about their epoch.

## World-Model Refs

The status payload also reports root-owned world-model artifact refs when present:

- `runtime/state/atlas/world-model.snapshot.latest.json`
- `runtime/state/atlas/world-model.attention.latest.json`

Those artifacts are the global snapshot layer above descriptors and receipts. Status remains descriptor-backed, but it may report the current snapshot and attention digests for clients that need one stable read surface.

## Open Merge Rule

A merge request remains open until a registered `atlas.stack.supervisor-consumer.v1` descriptor closes the same `merge_request_id`.

## Trust Surface Rule

Knowledge status output is metadata-only for quarantined surfaces. The status view must never hydrate raw Verta evidence or derived promotion text for those surfaces.
