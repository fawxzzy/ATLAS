# Cortex MVP Inventory

Scoped inventory of the current stack-root Cortex surface as of 2026-04-26.

## Surface Map

| Area | Current surface | Purpose |
| --- | --- | --- |
| Runtime artifacts | `runtime/cortex/artifacts/**` | Descriptor-backed runtime evidence for sessions, conversations, worker artifacts, capability profiles, merge requests, state snapshots, and legacy backfills. |
| Kernel seed artifacts | `runtime/cortex/kernel*.json` | Descriptive Wave 1 seed files for Cortex posture, rule registry, and proof summary examples. |
| Worker context | `runtime/cortex/context/**` | Deterministic per-assignment context packets. |
| Knowledge query plane | `runtime/cortex/query/knowledge/bundle.json` | Promoted knowledge bundle consumed by worker-context generation. |
| Supervisor lane | `runtime/cortex/supervisor/**` | Read-only merge-request artifacts and handoff refs for worker conflict handling. |
| Knowledge catalog | `runtime/cortex/catalog/knowledge/**` | Runtime catalog descriptors for promoted and adjacent knowledge archives. |
| Working memory catalog | `runtime/cortex/catalog/memory/working-memory.latest.json` | Normalized memory index built from `docs/memory/**`. |
| Playbook catalog | `runtime/cortex/catalog/playbooks/**` | Runtime playbook inventory / catalog lane. |
| Root state outputs | `runtime/state/atlas/world-model.snapshot.latest.json`, `runtime/state/atlas/world-model.attention.latest.json` | Consolidated world-model outputs derived from descriptors, receipts, registry, and working memory. |
| Cortex ops scripts | `ops/cortex/**` | Deterministic builders, supervisor, status renderer, artifact registration, memory indexing, and world-model generation. |

## Ops Modules

| Module | Current role | Main inputs | Main outputs |
| --- | --- | --- | --- |
| `ops/cortex/_artifacts.py` | Shared descriptor and digest helpers. | JSON payloads from runtime artifacts, `stack.yaml`, `runtime/cortex/**`, `runtime/state/atlas/**`, `runtime/receipts/**`, `docs/knowledge/promotions/**`. | Descriptor JSON under `runtime/cortex/artifacts/**`. |
| `ops/cortex/register_artifacts.py` | Batch descriptor registration for explicit artifact paths. | Artifact paths or default runtime surfaces. | Descriptor files in `runtime/cortex/artifacts/**` plus a summary on stdout. |
| `ops/cortex/build_worker_context.py` | Deterministic worker-context builder. | `runtime/cortex/query/knowledge/bundle.json`, promoted docs, runtime knowledge catalogs, latest knowledge receipts, assignment metadata. | `runtime/cortex/context/<assignment_id>.json`. |
| `ops/cortex/supervise_workers.py` | Read-only worker conflict supervisor. | Worker assignment and status artifacts, `stack.lock.yaml`, touched ranges, forbidden globs. | Merge-request artifacts in `runtime/cortex/supervisor/**` and a JSON report on stdout. |
| `ops/cortex/index_working_memory.py` | Working-memory validator and catalog builder. | `docs/memory/plans/**`, `docs/memory/decisions/**`, `docs/memory/initiatives/**`, `docs/memory/hypotheses/**`. | `runtime/cortex/catalog/memory/working-memory.latest.json`. |
| `ops/cortex/render_status.py` | Stack status read model. | Descriptors from `runtime/cortex/artifacts/**`, registry bundle, working memory catalog, lockfile, latest receipts, repo inventory. | Status JSON on stdout; derived attention, inventory, residue, and lock-hygiene views. |
| `ops/cortex/world_model.py` | World-model and attention snapshot builder. | Descriptors, registry bundle, latest event/knowledge/validation receipts, working memory catalog, render-status output. | `runtime/state/atlas/world-model.snapshot.latest.json`, `runtime/state/atlas/world-model.attention.latest.json`, emitted observations. |
| `ops/cortex/build_world_model.py` | Thin wrapper around world-model generation and descriptor registration. | Descriptor root plus the current runtime surface. | Same world-model outputs plus registered descriptors for the generated state files. |
| `ops/cortex/kernel.py` | Descriptive Cortex kernel seed loader for posture, rules, and proof summaries. | `runtime/cortex/kernel.state-model.seed.v1.json`, `runtime/cortex/kernel.rule-registry.seed.v1.json`, `runtime/cortex/kernel.proof-summary.examples.v1.json`. | Typed Cortex kernel primitives consumed by tests and future planning/proof layers. |

## Inputs And Outputs

### Inputs

- `stack.yaml` is the root contract for Cortex ownership and path policy.
- `stack.lock.yaml` is the lock digest used by worker assignment and supervisor validation.
- `runtime/cortex/query/knowledge/bundle.json` is the query-first bundle for worker context selection.
- `docs/knowledge/promotions/**` and `runtime/cortex/catalog/knowledge/**` feed query hydration.
- `runtime/receipts/knowledge/**/latest.json`, `runtime/receipts/events/**/latest.json`, and `runtime/receipts/validation/stack-validation.latest.json` feed status and world-model synthesis.
- `docs/memory/**` feeds working-memory normalization.
- `runtime/atlas/sessions/**`, `runtime/atlas/proposed-sessions/**`, `runtime/lifeline/worker-execution/**`, and `runtime/state/atlas/**` are descriptor sources for registration and read models.

### Outputs

- Descriptor artifacts land in `runtime/cortex/artifacts/**`.
- Worker context artifacts land in `runtime/cortex/context/**`.
- Supervisor merge-request artifacts land in `runtime/cortex/supervisor/**`.
- Working-memory catalog output lands in `runtime/cortex/catalog/memory/working-memory.latest.json`.
- World-model snapshot and attention output land in `runtime/state/atlas/world-model.snapshot.latest.json` and `runtime/state/atlas/world-model.attention.latest.json`.

## Validation Hooks

| Surface | Validation behavior |
| --- | --- |
| `build_worker_context.py` | Requires query bundle schema `atlas.knowledge.query-bundle.v1`, normalizes query terms, ranks deterministically, and stamps a stable content digest. |
| `index_working_memory.py` | Validates per-kind contract versions, required fields, timestamp format, allowed fields, and duplicate memory IDs before writing the catalog. |
| `register_artifacts.py` / `_artifacts.py` | Only registers known JSON contract/schema versions and skips unreadable or unrecognized payloads. |
| `supervise_workers.py` | Validates worker assignment/status contract versions, requires the assignment `stack_lock_digest` to match the current root lock, checks supported worker states, requires `touched_ranges` to be an array, and flags overlap / digest drift / forbidden-scope violations. |
| `render_status.py` | Derives canonical current-state views from descriptors, selects the latest active session, resolves canonical merge requests, and computes lock hygiene plus attention summaries. |
| `world_model.py` | Rebuilds working memory when valid, syncs observations without duplicating canonical source/status keys, and synthesizes snapshot and attention outputs from explicit receipts and descriptors. |

## Notable Legacy References

- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md` still names `repos/fawxzzy-atlas/**` as canonical platform doctrine and mentions `repos/cortex` as adjacent historical context.
- `docs/ops/CORTEX-SUPERVISOR-RUNBOOK.md` still mentions `repos/cortex` as historical context; that is consistent with the boundary docs but it is not an active owner surface.
- `docs/knowledge/QUERY-CONTRACT.md`, `docs/ops/ATLAS-CODEX-CONTEXT-RUNBOOK.md`, and several runtime context artifacts still reference `runtime/cortex/query/knowledge/bundle.json` directly, which is fine because that bundle is the current generated query plane.
- Runtime memory and catalog data still includes `personal--verta-core` and `personal--verta-core-sanitized`; those are intentionally quarantined / metadata-only surfaces, not active Cortex implementation truth.

## MVP Gap List

| Gap | Why it still matters |
| --- | --- |
| No single Cortex kernel entrypoint | The surface is still a collection of builders and read models rather than one clear project-intelligence core. |
| No unified memory/index abstraction | Working memory, query bundle, runtime catalogs, and receipts are separate lanes instead of one coherent memory model. |
| No planner that emits bounded worker lanes | The supervisor and context builder help with scope, but Cortex does not yet generate PR-sized work plans as a first-class product surface. |
| No receipt writer / proof receipt layer owned by Cortex | Cortex can read receipts and state, but proof-passing and action receipts still live in adjacent contracts. |
| No formal connector layer | GitHub / Vercel / repo adapters are not surfaced as a stable Cortex Link contract yet. |
| No explicit state ledger for latest-clean-step / blocked-lane tracking | The status model can infer state, but it does not yet present a dedicated, durable Cortex control ledger. |
| Broad stack-debt references remain in docs and catalogs | Historical `repos/*` references still need gradual cleanup, but they should not be treated as a blocker for the MVP slice. |

## Bottom Line

Cortex is already a real read-only coordination runtime with deterministic builders, a supervisor, a status read model, a memory catalog, and world-model outputs. Wave 1 now also has explicit seed artifacts for posture, rules, and proof summaries. What is still missing for the MVP is not more breadth; it is the next layer that turns those primitives into state reading, context assembly, bounded planning, proof interpretation, and receipt emission in one clear product surface.
