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

## Command

Render the global view:

```powershell
python .\ops\cortex\render_status.py
```

Render one session:

```powershell
python .\ops\cortex\render_status.py --session-id <session_id>
```

## Governed Surface View

The status renderer exposes governed surface identity from descriptors only:

- session manifests declare the session's governed surfaces
- worker descriptors expose `tool_id`, optional `extension_id`, and `registry_digest`
- receipt descriptors expose the same governed identity for the closing execution step
- the top-level registry section reports the current registry digest and entry counts

## Open Merge Rule

A merge request remains open until a registered `atlas.stack.supervisor-consumer.v1` descriptor closes the same `merge_request_id`.

## Trust Surface Rule

Knowledge status output is metadata-only for quarantined surfaces. The status view must never hydrate raw Verta evidence or derived promotion text for those surfaces.
