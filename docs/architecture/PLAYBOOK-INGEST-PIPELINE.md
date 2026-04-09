# Playbook Ingest Pipeline

This document defines the stack-owned ingest path for third-party playbooks and other external playbook content packs.

## Design Goal

Third-party playbooks are treated as external content packs, not as code to unpack into active repos and not as hidden state to merge into `repos/cortex`.

The ingest pipeline is:

1. import
2. evaluate
3. normalize
4. catalog
5. selectively adopt or reject

Each stage has its own path lane.

## Path Lanes

| Stage | Path | Purpose |
| --- | --- | --- |
| import | `data/imports/playbooks/` | raw imported pack plus source manifest |
| evaluation doctrine | `docs/playbooks/` | human-readable notes, policy, and catalog decisions |
| runtime catalog | `runtime/cortex/catalog/playbooks/` | machine-readable normalized catalog entries for future orchestration |

Nothing in this flow writes into active application repos during this pass.

## Import Stage

Imported content should arrive as a self-contained source pack under:

- `data/imports/playbooks/<source>/<slug>/`

Recommended contents:

- original files exactly as received
- `IMPORT-MANIFEST.json`
- `SOURCE.txt` or equivalent provenance notes
- optional `LICENSE.txt`

The import stage preserves provenance. It does not normalize or rewrite semantics yet.

## Evaluation Stage

Evaluation is a stack-owned review step.

Questions to answer:

1. Is the pack safe to inspect locally?
2. Is it vendor-neutral enough to reuse?
3. Is it mostly policy, prompts, runbooks, or executable code?
4. Does it require secrets, daemons, or hidden installers?
5. Does it assume one AI vendor or one proprietary filesystem layout?
6. Does it belong in ATLAS as a reference, as a selectively adopted idea set, or as a rejected import?

Evaluation outputs belong in:

- `docs/playbooks/PLAYBOOK-CATALOG.md`
- `docs/playbooks/THIRD-PARTY-PLAYBOOK-POLICY.md`
- optional future per-pack review docs under `docs/playbooks/`

## Normalization Stage

Normalization converts accepted concepts into ATLAS-owned structured metadata without copying vendor-specific code into active repos.

Normalization outputs should capture:

- source pack id
- source origin
- review status
- risk flags
- extracted capabilities
- adoption candidates
- rejected features

Normalization result format is intentionally simple JSON so future tools can read it without a database.

Normalized outputs belong under:

- `runtime/cortex/catalog/playbooks/*.json`

Those files are runtime catalog products, not source imports.

## Catalog Stage

The catalog is the bridge between human review and future machine recommendation.

Catalog record states:

- `imported`
- `evaluated`
- `normalized`
- `adopted_partially`
- `rejected`

Catalog records should capture why a pack landed in its current state.

## Selective Adoption

Selective adoption means:

- ATLAS documents the pattern in stack-owned docs
- ATLAS may create its own handler, wrapper, schema, or runbook inspired by the pack
- ATLAS does not transplant the vendor's internal folder conventions into stack truth
- repo changes happen only later, and only through normal scoped work

Adoption target examples:

- a reusable review checklist
- a portable validation idea
- a metadata convention
- an event type extension proposal

Non-adoption examples:

- a vendor-specific installer
- a hidden daemon runner
- a repo mutation macro that assumes one model vendor

## Rejection Rules

Reject a pack when it is:

- unsafe to run
- dependent on proprietary hidden state
- tightly coupled to one AI vendor's local configuration
- built around unpacking files directly into active repos
- dependent on background services or secret material outside approved lanes

Rejection still keeps the raw import in `data/imports/playbooks/` for traceability unless policy says the import should be removed for legal or safety reasons.

## Future CORTEX Role

Future CORTEX may read the normalized catalog in `runtime/cortex/catalog/playbooks/` and recommend which packs or patterns are worth adopting next.

That future role is advisory until explicitly promoted.
