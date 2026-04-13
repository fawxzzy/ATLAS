# Knowledge Archive Imports

This directory is the raw intake lane for personal learning materials and other knowledge archives.

## Rules

- keep imported archives outside `repos/`
- stage incoming zips or folders under ATLAS before import, such as `tmp/scratch/`
- preserve original source artifacts in `raw/`
- use `extracted/` for inspection only
- do not execute imported notebooks, scripts, binaries, or installers
- record provenance, privacy, and review state in `IMPORT-MANIFEST.json`

## Recommended Layout

Create one folder per imported archive:

- `data/imports/knowledge/<source>/<slug>/`

Recommended contents:

- `IMPORT-MANIFEST.json`
- `raw/<archive>.zip` for zip inputs
- `raw/**` for folder inputs and loose-document bundles
- `extracted/**` for inspection copies
- `EVALUATION.json` after the risk scan

## Relationship To Other Lanes

- raw and extracted knowledge materials stay here
- promotion-safe derived knowledge lives in `docs/knowledge/promotions/`
- human review and policy live in `docs/knowledge/`
- normalized machine-readable metadata belongs in `runtime/cortex/catalog/knowledge/`
- pipeline receipts belong in `runtime/receipts/knowledge/`
