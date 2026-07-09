# Vercel Platform Observability Governance log and runtime-error inventory prompt-pack and worker handoff contract

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root docs-only prompt-pack contract`
- Control-plane checkpoint: `bf6b5829417cdb44d087c14d8fc002d193f42ba5`
- Marker movement: none

## Worker Objective

Implement one bounded helper/test pair so `ops/atlas/vercel_log_runtime_error_inventory.py` can validate sanitized Vercel log and runtime-error wrappers, enforce redaction and path safety, and emit deterministic advisory JSON for the governed Vercel project set without touching live Vercel state.

## Exact Files

The worker may touch only:

- `ops/atlas/vercel_log_runtime_error_inventory.py`
- `tests/test_atlas_vercel_log_runtime_error_inventory.py`

## Exact Input Contract

The helper must consume only root-relative wrapper inputs under:

- `tmp/atlas/vercel-observability/*.json`
- `tmp/atlas/vercel-observability/*.jsonl`
- `tmp/atlas/vercel-observability/*.ndjson`

Each wrapper or JSON Lines intake path must be validated against:

- one governed project mapping
- one admitted source class
- the log/runtime-error contract-freeze redaction rules
- no secret-bearing or mutation-bearing payload retention

The helper must reject:

- absolute input paths
- parent traversal
- protected paths
- unknown file extensions
- wrapper content outside the admitted source classes

## Exact Admitted Source Classes

The helper may admit only these source classes:

- `request_log`
- `runtime_log`
- `runtime_error_group`
- `build_log_summary`

The helper must reject unsupported source classes.

`build_log_summary` is admitted only when the wrapper content is already sanitized and does not carry raw secret-bearing build output.

## Exact CLI Contract

Required flags:

- `--input` repeatable, one or more root-relative `tmp/**` wrapper paths
- `--json` optional JSON-only stdout mode
- `--output` optional root-relative `tmp/**.json` output path
- `--strict` optional blocker-sensitive exit mode

The helper must reject:

- zero `--input` arguments
- absolute output paths
- parent traversal in output paths
- protected output paths
- output paths outside root-relative `tmp/**.json`

## Exact Helper Contract

The worker must implement a helper that:

1. reads the governing audit and contract receipts plus stack inventory truth
2. rejects wrapper paths outside admitted root-relative `tmp/**`
3. rejects malformed or non-object JSON wrapper records
4. rejects unknown governed project slugs, ids, names, or logical mappings
5. rejects unsupported source classes
6. rejects forbidden sensitive fields such as env values, token values, secrets, cookies, authorization headers, and raw request bodies
7. normalizes admitted route data to route or path patterns rather than raw personalized URLs when needed
8. classifies runtime-error clusters without opening owner-repo work
9. aggregates deterministic counts for projects, clusters, status families, and log records
10. reports blockers and warnings explicitly

## Exact Output Contract

The helper output must emit schema version:

```text
atlas.vercel_log_runtime_error_inventory.v1
```

Allowed statuses:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

Required top-level fields:

- `schema_version`
- `status`
- `safe_to_use`
- `captured_project_count`
- `project_count`
- `runtime_error_cluster_count`
- `log_record_count`
- `redaction_status`
- `projects`
- `clusters`
- `warnings`
- `blockers`
- `forbidden_fields_detected`
- `next_recommended_packet`

## Exact Project Summary Contract

Each admitted project summary may use only:

- `project_slug`
- `project_id`
- `environment`
- `source_classes`
- `deployment_ids`
- `route_pattern_count`
- `runtime_error_cluster_count`
- `log_record_count`
- `status_code_families`
- `levels`
- `first_seen`
- `last_seen`
- `sample_count`
- `redaction_status`

## Exact Cluster Summary Contract

Each admitted cluster summary may use only:

- `project_slug`
- `deployment_id`
- `environment`
- `source_class`
- `cluster_label`
- `route_pattern`
- `status_code_family`
- `level`
- `first_seen`
- `last_seen`
- `occurrence_count`
- `sample_count`
- `redaction_status`

The helper may not emit:

- env values
- token values
- secret values
- cookies
- authorization headers
- raw request bodies
- raw customer or payment payloads
- unredacted sensitive stack traces

## Exact Allowed Inputs

The helper may read only:

- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-PROJECT-INVENTORY-COVERAGE-RECONCILIATION-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-LOG-AND-RUNTIME-ERROR-INVENTORY-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-LOG-AND-RUNTIME-ERROR-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- explicitly named sanitized wrapper files under `tmp/atlas/vercel-observability/`

## Exact Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_vercel_log_runtime_error_inventory -v`
2. one root-safe helper proof command against synthetic sanitized wrapper input under `tmp/atlas/vercel-observability/`
3. `python ops/validation/validate_stack.py`
4. `git status --short`
5. `git diff --name-only`

The worker may add focused helper proof invocations, but must not widen into live Vercel capture.

## Exact Required Proof Matrix

The worker proof must cover at least:

1. valid sanitized wrapper input is accepted
2. multiple governed projects aggregate correctly
3. one runtime-error cluster can be summarized without raw sensitive payload
4. the Fitness webhook route cluster remains observability evidence only
5. env-value patterns are rejected
6. token-value patterns are rejected
7. cookie or authorization-header patterns are rejected
8. raw request-body patterns are rejected unless absent or redacted
9. unknown project mappings are rejected
10. unsupported source classes are rejected
11. input paths outside `tmp/**` are rejected
12. absolute output paths are rejected
13. protected output paths are rejected
14. safe `tmp/**.json` output is accepted
15. deterministic JSON ordering is preserved
16. `--strict` returns nonzero on blockers

## Exact Forbidden Authority

The worker must not:

- query live Vercel APIs
- run `vercel logs` or other live Vercel CLI capture by default
- touch owner repos
- touch Fitness, Mazer, DiscordOS, Trove, or Foundation working trees
- read secrets or `.env*`
- touch deploy, domain, alias, env, drain, webhook, or other platform-mutation surfaces
- move markers
- emit final receipts
- add helper files outside the admitted two-file surface
- widen into current-state, marker-table, or restart-guide mirror edits

## Exact Stop Conditions

Stop and return without implementation if the worker would require:

- live Vercel API access from repo code
- live token use
- owner-lane mutation
- deploy, domain, env, secret, or webhook authority
- marker movement
- broader helper family expansion beyond the admitted single helper/test pair
- committed `tmp/**` artifacts

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance log and runtime-error inventory implementation-readiness closeout and worker routing
```
