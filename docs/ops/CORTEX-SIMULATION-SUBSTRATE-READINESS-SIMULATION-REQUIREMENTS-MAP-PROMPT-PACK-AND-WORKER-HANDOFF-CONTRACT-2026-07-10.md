# Cortex Simulation Substrate Readiness simulation requirements map prompt-pack and worker handoff contract

- Date: `2026-07-10`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root docs-only prompt-pack and worker handoff contract`
- Scope: `freeze the exact implementation contract for one root-owned, read-only simulation requirements-map helper and its proof surface without implementing the helper or moving the marker`
- Control-plane checkpoint: `main@461bc5a8`
- Marker movement: none

## Why This Packet Exists

The research contract and first-implementation admission are now durable.

This packet exists to freeze the exact worker contract before any implementation worker is routed.

It must leave:

- `Sandbox Simulation Readiness` held at `99%`
- `Cortex Simulation Substrate Readiness` at `0%`
- `Vercel Platform Observability Governance` as the broader selector fall-through

unchanged.

## Durable Inputs Confirmed

This packet inherits:

- `docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md`
- `docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-SIMULATION-SUBSTRATE-2026-07-09.md`
- `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`

The admitted future files remain exactly:

- `ops/cortex/simulation_substrate_requirements.py`
- `tests/test_cortex_simulation_substrate_requirements.py`

No second helper family is admitted.

## Inherited Validation Baseline

The inherited root validation baseline is:

- `critical=0`
- `error=0`
- `warning=5`
- `info=0`

The five inherited warnings remain one debt class only:

- category: `atlas-root-path`
- debt class: `path-discipline-leaks`
- path: `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-RECEIPT-INDEX-AND-RESTART-TRUTH-RECONCILIATION-2026-07-09.md`
- line numbers: `56`, `58`, `62`, `66`, `71`

This packet may not introduce any new warning class or increase the warning count above `5`.

## Worker Objective

The future helper must:

1. read approved root-owned research, receipt, architecture, doctrine, and governance sources
2. produce a deterministic simulation-substrate requirements map
3. classify required versus optional substrate requirements
4. surface governance gaps, missing requirements, warnings, and blockers explicitly
5. classify future project-adapter requirements without reading or mutating owner repos
6. emit advisory output only

The future helper must not:

- run a simulation
- run agents
- generate scenes, media, or IP outputs
- invoke external APIs or networks by default
- train or fine-tune models
- mutate ATLAS root truth, owner repos, deploy surfaces, secrets, or markers

## Exact Future Worker Files

The exact future implementation files are:

- `ops/cortex/simulation_substrate_requirements.py`
- `tests/test_cortex_simulation_substrate_requirements.py`

No other implementation file is admitted by this packet.

## Admitted Source Surfaces

The future helper may read only approved root-owned sources such as:

- `docs/ops/**` receipts in the Simulation, Cortex, and routing chain
- `docs/architecture/**`
- `docs/PLAYBOOK_NOTES.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/atlas-book/05-receipt-index.md`
- `AGENTS.md`
- explicit safe test fixtures under `tmp/**` or test-owned fixture paths

These sources are admitted because they are:

- durable
- root-owned
- reproducible
- authority-bounded

## Excluded Source Surfaces

The helper must reject or ignore by policy:

- owner-repo source trees
- hidden transcript or chat state
- raw user or customer data
- `.env*`
- `.vercel`
- `.playwright-mcp`
- `archive/**`
- `secrets/**`
- Vercel or Supabase live data
- deployment logs
- browser profiles
- copyrighted media corpora
- generated AI media
- network or API inputs

## Exact CLI Contract

The first worker CLI is:

```text
python ops/cortex/simulation_substrate_requirements.py --json --source <root-relative-path> --source <root-relative-path> --output <root-relative-path> --strict
```

Required flags:

- `--json`
- repeatable `--source <root-relative-path>`
- `--output <root-relative-path>`
- `--strict`

Not admitted in this packet:

- `--project-scope`
- `--schema-only`
- any network or live-provider flags

Those can only be admitted by a later receipt if a narrower need appears.

## JSON Output Contract

The helper must emit deterministic JSON with these top-level fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `source_digests`
- `research_basis`
- `requirements`
- `core_primitives`
- `governance_primitives`
- `optional_extensions`
- `project_adapter_requirements`
- `evaluation_requirements`
- `authority_denials`
- `ethical_risks`
- `ip_rights_risks`
- `privacy_risks`
- `missing_requirements`
- `warnings`
- `blockers`
- `safe_to_use`
- `next_recommended_packet`

Each requirement record must support:

- `requirement_id`
- `category`
- `name`
- `description`
- `priority`
- `required`
- `source_refs`
- `proof_required`
- `authority_boundary`
- `status`
- `blocked_reason`

## Status Classes

The only admitted status classes are:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## Exit-Code Policy

The helper must exit:

- `0` for `ok`
- `0` for `advisory_gap` without `--strict`
- nonzero for `advisory_gap` with `--strict`
- nonzero for `blocker`
- nonzero for `internal_error`

## Input And Output Path Guards

The helper must:

- reject absolute source paths
- reject absolute output paths
- reject any path outside the ATLAS root
- reject owner-repo roots
- reject protected or secret-bearing paths
- reject `.env*`, `.vercel`, `.playwright-mcp`, and `archive/**`
- allow explicit safe output only under `tmp/**.json`
- refuse to write any output when `--output` is omitted
- avoid writing any runtime-latest or restart-mirror file by default

## Deterministic Output Requirements

The helper must:

- preserve deterministic JSON field ordering
- preserve deterministic requirement ordering
- preserve deterministic source digest ordering
- emit the same results for the same committed inputs
- fail closed rather than invent missing doctrine

No hidden transcript memory may affect output.

## Requirements Taxonomy

The first requirements taxonomy must cover these core simulation primitives:

- `scenario`
- `world_state`
- `agent`
- `agent_identity`
- `agent_goal`
- `observation`
- `memory`
- `memory_retrieval`
- `reflection`
- `plan`
- `action`
- `environment_feedback`
- `execution_error`
- `self_verification`
- `evaluation`
- `replay`
- `termination_condition`

## Governance Taxonomy

The first governance taxonomy must cover:

- `source_provenance`
- `rights_and_ip_boundary`
- `human_approval_boundary`
- `authority_denials`
- `safety_boundary`
- `privacy_boundary`
- `secret_boundary`
- `owner_lane_boundary`
- `proof_reference`
- `receipt_reference`
- `determinism_requirement`
- `auditability_requirement`
- `retention_boundary`

## Project-Adapter Taxonomy

The helper may describe future adapter requirements only for:

- `atlas_governance`
- `fitness_scenario`
- `mazer_gameplay`
- `discordos_community`
- `platform_incident`

These adapter records are requirement surfaces only.

The helper must not:

- inspect those owner repos
- claim any adapter exists
- claim implementation progress
- claim live adoption

## Ethical, IP, And Safety Boundaries

The helper must preserve explicit denial for:

- unauthorized IP or character simulation
- media generation
- user impersonation
- synthetic-human misrepresentation
- owner-lane mutation
- hidden-data ingestion
- authority creep from scenario reasoning into execution
- privacy or secret leakage

## Authority Denials

The helper must always emit authority denials for:

- owner-repo mutation
- Vercel mutation
- Supabase mutation
- deploy execution
- workflow dispatch or edit
- secret handling
- final receipt emission
- marker movement
- `_stack` dispatch
- simulation execution
- model training
- live-user-data use

## Proof Matrix

The future worker must prove at least:

1. valid approved root-owned research sources are accepted
2. research-contract requirements are mapped
3. core primitives include observation, memory, reflection, planning, action, and evaluation
4. governance primitives include provenance, rights or IP, human approval, privacy, safety, and proof references
5. project adapters are emitted as requirements only
6. owner-repo source paths are rejected
7. hidden transcript or chat source paths are rejected
8. `.env*` source paths are rejected
9. Vercel or Supabase live-data source classes are rejected
10. unauthorized IP or media source classes are rejected
11. model-training instructions are classified as forbidden
12. simulation execution requests are classified as out of scope
13. absolute source paths are rejected
14. absolute output paths are rejected
15. protected output paths are rejected
16. safe `tmp/**.json` outputs are accepted
17. deterministic JSON ordering holds
18. missing required requirements produce `advisory_gap`
19. malformed sources produce `blocker` or `internal_error` consistently
20. `--strict` exits nonzero on advisory gaps or blockers
21. authority denials are always emitted
22. no files are written without explicit `--output`
23. no network or API calls are required
24. the inherited warning count and warning class set are not increased

## Stop Conditions

Stop without claiming implementation readiness if:

- required durable receipts are missing
- the admitted helper paths drift from the first-implementation admission
- root validation introduces any critical or error finding
- the warning count exceeds `5`
- any new warning class appears
- implementation would require owner-repo inputs
- implementation would require secret, deploy, workflow, or provider access
- implementation would require hidden transcript or live-user-data access
- implementation would widen into simulation execution

## Exact Next Packet

The next exact packet is:

```text
Cortex Simulation Substrate Readiness simulation requirements map implementation-readiness closeout and worker routing
```

## Marker Decision

No marker moves.

`Cortex Simulation Substrate Readiness` remains `0%`.

Reason:

- this packet freezes worker doctrine only
- no helper is implemented yet
- no proof-backed requirements map exists yet
- no ratchet receipt has been published

## Validation

Validated during this prompt-pack pass:

- `python ops/validation/validate_stack.py` -> `critical=0 error=0 warning=5 info=0`
- `python ops/atlas/marker_knockout_selector.py --format json`
- `python ops/atlas/marker_knockout_selector.py --format markdown`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python -m unittest tests.test_atlas_marker_knockout_selector -v`

## Completion

Completion: `100%` for the prompt-pack and worker handoff contract itself.

No owner repo was mutated.
No platform surface was mutated.
No secret, deploy, workflow, or protected surface was touched.
