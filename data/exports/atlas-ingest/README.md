# ATLAS Ingest Exports

This folder may contain copied CSV exports used for local ingest review, such as:

- `atlas-ingest-registry.csv`
- `descendant-registry.csv`

These copied exports are not durable in git by default because the root `.gitignore` ignores `data/**`.

Current rule:

- treat the CSV copies here as local review evidence
- keep the tracked ingest posture in stack docs such as `docs/architecture/ATLAS-INGEST-AND-CLEANUP-GUARDRAILS.md`
- only unignore or relocate an export when a workflow intentionally needs that export itself to become tracked
