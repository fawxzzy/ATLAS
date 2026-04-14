# ATLAS Status Runbook

The ATLAS status view is rendered from artifact descriptors only.

## Contract

- status reads `runtime/cortex/artifacts/**`
- status does not inspect raw session logs
- status does not infer worker completion from terminal output

## Questions Answered

The current status read model answers:

- what session is active
- what descriptors exist
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

## Open Merge Rule

A merge request remains open until a registered `atlas.stack.supervisor-consumer.v1` descriptor closes the same `merge_request_id`.

## Trust Surface Rule

Knowledge status output is metadata-only for quarantined surfaces. The status view must never hydrate raw Verta evidence or derived promotion text for those surfaces.
