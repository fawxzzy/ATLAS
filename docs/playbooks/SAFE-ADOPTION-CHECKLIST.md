# Safe Adoption Checklist

Use this checklist before moving any idea from an imported pack into ATLAS-owned artifacts.

- Raw vendor files remain under `data/imports/playbooks/`.
- Nothing from the pack was copied into `repos/cortex` or any other repo.
- No vendor hook, installer, daemon, scheduler, or background worker was executed.
- Secrets are not required to import, evaluate, or normalize the pack.
- Lifecycle events remain in `ops/events/`; pack evaluation logic remains in `ops/playbooks/`.
- The adoption target is an ATLAS-owned wrapper, schema, doc, checklist, or validator.
- Vendor-specific conventions are translated into stack-owned abstractions before adoption.
- `IMPORT-MANIFEST.json` exists and records the original filename and checksum for zip inputs.
- `EVALUATION.json` records all required risk flags.
- The normalized catalog entry contains metadata only, not vendor code.
- `docs/playbooks/PLAYBOOK-CATALOG.md` reflects the current status.
- `python ops/playbooks/validate_playbook_catalog.py` passes.
- `python ops/validation/validate_event_contracts.py` still passes.
- `python ops/validation/validate_stack.py` still passes or any pre-existing failures are explicitly recorded.
