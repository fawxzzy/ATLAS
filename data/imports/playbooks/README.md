# Playbook Imports

This directory is the raw intake lane for third-party playbook content packs.

## Rules

- keep imports outside active repos
- preserve original structure and provenance
- do not unpack vendor packs into `repos/cortex`
- do not treat imported scripts as approved runtime code
- do not store secrets here

## Recommended Layout

Create one folder per source pack:

- `data/imports/playbooks/<source>/<slug>/`

Recommended contents:

- original files as imported
- `IMPORT-MANIFEST.json`
- provenance notes such as `SOURCE.txt`
- optional license notes

## Relationship To Other Lanes

- raw imports stay here
- human review lives in `docs/playbooks/`
- normalized runtime catalog entries belong in `runtime/cortex/catalog/playbooks/`
