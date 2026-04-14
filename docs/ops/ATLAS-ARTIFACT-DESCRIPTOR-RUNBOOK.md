# ATLAS Artifact Descriptor Runbook

`atlas.artifact.descriptor.v1` is the thin artifact-identity layer for governed ATLAS artifacts.

## Purpose

- give important artifacts a stable digest identity
- expose typed metadata without reading logs
- keep the first pass as descriptor registry, not a full CAS

## Descriptor Lane

- descriptor files live under `runtime/cortex/artifacts/`
- descriptor paths mirror the source artifact path
- descriptor identity is the artifact byte digest in `digest`

## Registered Artifact Types

Current registry coverage includes:

- session manifest
- worker context
- worker assignment
- worker status
- merge request
- supervisor merge completion
- capability profile
- privileged-action request
- approval receipt
- execution receipt
- knowledge runtime catalogs needed for trust/status views
- world-model state and attention snapshots under `runtime/state/atlas/`

## Determinism

The descriptor output must be stable for unchanged artifact bytes and unchanged policy-derived metadata.

Rules:

- `digest` is the SHA-256 of the artifact bytes
- no registration wall-clock timestamp is written into the descriptor
- descriptor metadata is extracted only from artifact bytes, path, and stable policy rules

## Command

Register descriptors for the default runtime lanes:

```powershell
python .\ops\cortex\register_artifacts.py
```

Register descriptors for a specific session:

```powershell
python .\ops\cortex\register_artifacts.py --artifact-path runtime/atlas/sessions/<session_id>
```

## Metadata Rules

- descriptor metadata may grow additively
- descriptor metadata must not leak raw imported evidence
- quarantined Verta knowledge surfaces remain `trust_class = untrusted`
- sanitized-but-not-promoted Verta surfaces remain `regulated_artifact_class = metadata_only`
