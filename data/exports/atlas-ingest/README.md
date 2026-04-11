# ATLAS Ingest Exports

This folder may contain copied CSV exports used for local ingest review, such as:

- `atlas-ingest-registry.csv`
- `descendant-registry.csv`

These copied exports are not durable in git by default because the root `.gitignore` ignores `data/**`.

Current rule:

- treat CSV and JSON exports here as local review evidence by default
- keep the tracked ingest posture in stack docs such as `docs/architecture/ATLAS-INGEST-AND-CLEANUP-GUARDRAILS.md`
- promote only exact files, one by one, after they meet the export tracking gate in that guardrails doc
- do not blanket-unignore `data/**` just to track review artifacts early
