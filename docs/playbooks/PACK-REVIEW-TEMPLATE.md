# Pack Review Template

Use this template for each third-party playbook pack after `EVALUATION.json` is generated.

## Pack

- `pack_id`:
- `source_name`:
- `import_dir`:
- `reviewed_at`:
- `reviewer`:

## Provenance

- original input:
- import manifest:
- license notes:
- provenance confidence:

## Risk Flags

- `vendor_lock`:
- `hook_risk`:
- `daemon_risk`:
- `repo_mutation_risk`:
- `secret_dependency`:
- `executable_content`:

## Safety Decision

- safety:
- status:
- normalize allowed:
- no-execute guarantee confirmed:

## Adoption Surface

- allowed ideas:
- rejected ideas:
- notes for ATLAS-owned rewrite:

## Required Follow-Up

- refresh `docs/playbooks/PLAYBOOK-CATALOG.md`
- update `runtime/cortex/catalog/playbooks/` if accepted
- document remaining blockers before adoption
