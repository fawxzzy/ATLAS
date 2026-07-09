# Vercel Platform Observability Governance read-only project inventory prompt-pack and worker handoff contract

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root docs-only prompt-pack contract`
- Control-plane checkpoint: `f210d703f5df370a48d7ee68276661a163752f31`
- Marker movement: none

## Worker Objective

Implement one bounded helper/test pair so `ops/atlas/vercel_observability_project_inventory.py` can validate root-relative Vercel project-inventory wrappers and summarize only the admitted read-only fields for governed ATLAS projects.

## Exact Files

The worker may touch only:

- `ops/atlas/vercel_observability_project_inventory.py`
- `tests/test_atlas_vercel_observability_project_inventory.py`

## Exact Input Contract

The worker must consume only root-relative wrapper inputs under:

- `tmp/atlas/vercel-observability/*.json`

Each wrapper must be validated against:

- one consistent team identity
- one governed project mapping
- one bounded posture-class set
- admitted deployment/log/error/observability fields only

## Exact Helper Contract

The worker must:

1. read the governing audit and contract-freeze receipts plus stack repo inventory
2. reject wrapper paths outside root-relative `tmp/**.json`
3. reject malformed or non-object JSON wrappers
4. reject inconsistent team ids or team names across the run
5. reject unknown project ids, names, or repo logical ids
6. reject duplicate captures for the same governed project in a single run
7. reject forbidden sensitive keys such as env values, token values, or secret values
8. emit deterministic summary output for admitted project captures only
9. report missing governed project captures explicitly

## Exact Output Contract

The helper output must include:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_receipts`
- `input_count`
- `team`
- `posture_classes`
- `captured_project_count`
- `projects`
- `missing_projects`
- `blockers`
- `warnings`

The helper may not emit:

- env values
- token values
- secret values
- request bodies
- credential-bearing headers

## Exact Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_vercel_observability_project_inventory -v`
2. `python ops/atlas/vercel_observability_project_inventory.py --json --input tmp/atlas/vercel-observability/proof-sample.json`
3. `python ops/validation/validate_stack.py`
4. `git status --short`
5. `git diff --name-only`

## Exact Forbidden Authority

The worker must not:

- query live Vercel APIs
- touch owner repos
- touch Fitness or Mazer working trees
- read secrets or `.env*`
- touch deploy or platform mutation surfaces
- move markers
- emit final receipts
- add new helper files, fixture files, or schema files outside the admitted two-file surface
- widen into current-state or restart-guide mirrors

## Exact Stop Conditions

Stop and return without implementation if the worker would require:

- new files beyond the helper and test
- direct Vercel API access from repo code
- live token use
- owner-lane mutation
- deploy, domain, env, or secret authority
- packet invention outside the admitted Vercel project-inventory chain

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance read-only project inventory implementation-readiness closeout and worker routing
```
