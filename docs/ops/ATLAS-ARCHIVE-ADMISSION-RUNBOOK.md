# ATLAS Archive Admission Runbook

This runbook governs how ATLAS root handles zip snapshots, backup drops, and other archive-derived material that should not silently become source-repo truth.

## Rules

- Catalog the surface first in `docs/registry/ATLAS-ARCHIVE-REGISTRY.json`.
- Keep raw archive material as provenance-only unless a named owner and deterministic verification path exist.
- Route bundle and patch backups to `packages/bundles` and `packages/patches`.
- Route source snapshots to `packages/snapshots`.
- Keep quarantined historical archives, including `repos/Verta-Core.zip`, blocked from release and direct owner adoption.
- Do not admit mixed-owner or unknown-owner archives directly into `repos/<owner>` from a root session.

## Current Governed Surfaces

| Surface id | Path | Current posture | Next action |
| --- | --- | --- | --- |
| `cortex_playbook_snapshot_archive` | `repos/CORTEX-AND-PLAYBOOK-20260408.zip` | Reference-only manifest surface, not present in the current checkout | Split owner boundary before any extract or relocation |
| `dev_workspace_snapshot_archive` | `repos/dev.zip` | Reference-only manifest surface, not present in the current checkout | Catalog provenance before any extract or relocation |
| `repo_backups_archive_surface` | `repos/repo-backups` | Direct current legacy backup surface | Treat as package-layer backup infrastructure and relocate on a deliberate cleanup lane |
| `verta_core_archive` | `repos/Verta-Core.zip` | Direct current quarantined archive surface | Keep metadata-only and derivative-only |

## Workflow

1. Classify the surface as one of: source snapshot, backup bundle or patch, archive docs, runner residue, or quarantined evidence.
2. Add or update the registry entry with current presence, owner scope, retention reason, and canonical destination.
3. Declare the surface in `stack.yaml` when it must remain stack-visible.
4. If the surface should stay outside normal repo flows, keep it in `stack_lock.excluded_surfaces`.
5. Only extract doctrine or owner truth after rewriting the material into an owner-repo artifact with explicit provenance and verification.

## Candidate Record Template

```json
{
  "behavior": "",
  "owner_repo": "",
  "why": "",
  "source_provenance": "",
  "seam_boundary": "",
  "inputs": [],
  "outputs": [],
  "rollback": "",
  "verification": "",
  "why_raw_stays_provenance_only": ""
}
```
