# ATLAS Event Handler Scaffold

Event handlers are optional, vendor-neutral adapters that run after schema validation.

## Discovery Rules

For an event type named `<event_type>`, the invoker checks these paths in order:

1. `ops/events/handlers/<event_type>.py`
2. `ops/events/handlers/<event_type>.ps1`

If no handler exists, the event is still accepted and a receipt is written with `handler.status = "skipped"`.

## Handler Input Contract

Handlers should accept a JSON payload file path.

Expected parameters:

- Python: `--payload-file <path> --atlas-root <path>`
- PowerShell: `-PayloadFile <path> -AtlasRoot <path>`

The JSON payload matches the schema-validated event envelope.

## Handler Output Contract

Handlers may write a JSON object to stdout with fields such as:

- `summary`
- `artifacts`
- `notes`
- `adopted_actions`

If stdout is empty, the invoker records an empty result object.

If the handler exits nonzero, the event receipt is still written but marked with `processing.status = "handler_failed"`.

## Recommended Handler Responsibilities

Good handler tasks:

- enrich a receipt with deterministic metadata
- trigger a stack-local follow-up artifact
- normalize imported playbook metadata
- run an explicit validator and summarize its result

Bad handler tasks:

- hidden background execution
- direct mutation of unrelated repos
- secret retrieval
- vendor-specific side channels that bypass receipts
