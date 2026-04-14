# ATLAS Tool Registry Runbook

The governed ATLAS runtime surface is rooted in machine-readable registry data, not prose-only docs.

## Registry Truth

- tool registry path: `docs/registry/ATLAS-TOOL-REGISTRY.json`
- extension registry path: `docs/registry/ATLAS-EXTENSION-REGISTRY.json`
- tool entry schema: `schemas/atlas.tool.catalog.entry.v1.json`
- extension entry schema: `schemas/atlas.extension.manifest.v1.json`

Atlas doctrine defines the stable public catalog and extension model. The root registry is the executable allowlist used by sessions, status, Lifeline, and Playbook.

## Ownership

- Atlas owns public naming, stability, and catalog doctrine
- the ATLAS root owns the machine-readable runtime registry snapshots
- Playbook enforces fail-closed policy against the registry
- Lifeline enforces the same registry at execution time
- `_stack` and root sessions may request only registered surfaces

## Current Registered Surfaces

The root registry currently seeds only shipped surfaces:

- `cortex.build_worker_context`
- `cortex.supervise_workers`
- `read_only_scan`
- `scoped_write.dry_run`

Unknown or speculative surfaces must not be added just to reserve names.

## Validation

Validate the registry bundle:

```powershell
python .\ops\atlas\validate_tool_registry.py
```

Inspect one registered tool:

```powershell
python .\ops\atlas\load_tool_registry.py --tool-id read_only_scan
```

The loader computes a deterministic bundle digest. Identical registry bytes must produce the same digest across repeated loads.

## Governed Artifact Rule

Every governed session, request, status, and receipt artifact must carry:

- `tool_id`
- `extension_id` when the surface is extension-backed
- `registry_digest`

These fields must refer to a registry entry that exists in the current root bundle. Governed flows fail closed when the surface is unknown, mismatched, untrusted, or not release-eligible.

## Trust Classes

- built-in trusted surfaces may appear in the root registry
- extension-backed trusted surfaces may appear only with a valid extension manifest entry
- untrusted or quarantined surfaces stay out of the trusted registry
- Verta remains metadata-only and untrusted; it is not a registrable governed surface

## Update Flow

1. update Atlas doctrine if the public contract changed
2. update the machine-readable registry under `docs/registry/`
3. validate the registry bundle
4. run Playbook and Lifeline verification for the new surface
5. run root ratchet validation

## Non-Goals

- no speculative tool registration
- no prose-only registry truth
- no trust promotion by runtime convention
