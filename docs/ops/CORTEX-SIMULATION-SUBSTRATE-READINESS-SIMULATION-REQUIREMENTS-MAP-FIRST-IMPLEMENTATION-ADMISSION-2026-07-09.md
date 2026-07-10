# Cortex Simulation Substrate Readiness simulation requirements map first-implementation admission

- Date: `2026-07-09`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Scope: `admit one future root-owned helper/test pair that can deterministically map the first Cortex Simulation requirements schema from frozen doctrine and receipts without implementing a simulator`
- Control-plane checkpoint: `main@f78d4bae`
- Marker movement: none

## Decision

Admit one future root-owned helper/test pair for Simulation requirements mapping.

The next exact packet is:

```text
Cortex Simulation Substrate Readiness simulation requirements map prompt-pack and worker handoff contract
```

This admission does not implement a helper, execute a simulation, mutate any repo, or move a marker.

## Objective

Freeze the smallest honest implementation slice that can convert the research contract into deterministic requirements output for a future Simulation substrate.

The first implementation is advisory only.

It must:

1. read root-owned simulation doctrine and receipt inputs
2. emit a deterministic requirements map for the first simulation schema
3. preserve authority-denial and data-surface boundaries explicitly
4. keep future project adapters and live data inputs out of scope
5. fail closed when doctrine inputs are missing or ambiguous

## Admitted Future Surfaces

Only these future files are admitted:

- `ops/cortex/simulation_substrate_requirements.py`
- `tests/test_cortex_simulation_substrate_requirements.py`

No other file is admitted by this packet.

## Why This Is Cortex Simulation Work

This lane is root-owned Cortex governance work because the future helper would operate only on:

- ATLAS-root receipts
- frozen simulation doctrine
- durable workflow-profile context
- root-owned marker and receipt truth

It would classify requirements.

It would not perform simulation.

## Why This Is Not Owner-Repo Work

This packet is not Fitness, Mazer, DiscordOS, Trove, Foundation, or Playbook implementation work because the admitted helper may only map substrate requirements from root-owned doctrine.

It may not:

- mutate owner repos
- inspect owner-repo private drift as simulation truth
- debug runtime behavior
- claim owner-side adoption
- consume live product records by default

## Admitted Scope

The future helper may do only this:

1. load the frozen simulation research contract
2. load the marker-admission and reselection context
3. derive the first schema classes and requirement groups
4. map admitted data surfaces and forbidden data surfaces
5. map admitted authority and forbidden authority
6. report open gaps, warnings, and blockers deterministically

The future helper may not:

- run agents
- generate scenes
- call external APIs
- read hidden transcripts
- inspect secret-bearing inputs
- perform scenario execution
- widen into project-specific adapters

## Required Root-Owned Inputs

The future helper may consume only root-owned, reproducible inputs such as:

- `docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md`
- `docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-SIMULATION-SUBSTRATE-2026-07-09.md`
- `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `AGENTS.md`
- `docs/atlas-book/05-receipt-index.md`

The first implementation is not admitted to depend on:

- hidden transcripts
- chat export archives
- owner-repo receipts as primary truth
- live product or platform queries
- uncommitted diffs
- raw user data

## Admitted First Schema Groups

The future helper may classify only these first schema groups:

- `scenario`
- `agent`
- `world_state`
- `memory`
- `reflection`
- `plan`
- `action`
- `observation`
- `evaluation`
- `safety_boundary`
- `proof_reference`

These are admitted because they are already frozen in the research contract.

## Admitted Future Output Shape

The future helper must emit deterministic advisory output only.

Minimum top-level output fields:

- `schema_version`
- `status`
- `safe_to_use`
- `requirement_group_count`
- `mapped_group_count`
- `unmapped_group_count`
- `requirement_groups`
- `admitted_data_surfaces`
- `forbidden_data_surfaces`
- `admitted_authority`
- `forbidden_authority`
- `warnings`
- `blockers`

Each requirement-group record must be able to carry:

- `group_id`
- `group_class`
- `summary`
- `required_fields`
- `admitted_inputs`
- `forbidden_inputs`
- `authority_notes`
- `future_adapter_notes`

The helper must fail closed rather than inventing missing doctrine truth.

## Required Safety Behavior

The future helper must:

- stay read-only
- preserve marker-write denial
- preserve owner-repo mutation denial
- preserve deploy/workflow/secret denial
- keep project-specific adapters explicit instead of implied
- keep ethical, IP, and authority risks visible instead of collapsing them into success claims

## Still Excluded

The future helper must continue to exclude:

- video-generation requirements
- copyrighted character libraries
- secret-bearing replay state
- project-specific live connector inputs
- simulation execution loops
- evaluation claims based on hidden session memory

These exclusions keep the first slice bounded to requirements mapping only.

## Expected CLI Posture

The future helper is admitted with this intended first interface:

- `python ops/cortex/simulation_substrate_requirements.py`
- `--json`
- `--output <root-relative tmp path>`
- `--strict`

These flags are admitted as the intended first surface and may be tightened by the next prompt-pack packet.

## Required Status Classes

Expected status classes:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## What The Future Helper Must Not Do

The future helper must not:

- run agents
- call external APIs
- read browser state
- inspect archived chat logs
- mutate repos
- stage, commit, or push
- emit final receipts
- move markers
- claim the simulation substrate is operational

## Proof Matrix For The Future Worker

The future implementation must prove at least:

1. deterministic classification of the first schema groups
2. deterministic admitted-data-surface output
3. deterministic forbidden-data-surface output
4. deterministic admitted-authority output
5. deterministic forbidden-authority output
6. explicit reporting of project-adapter deferral
7. failure-closed behavior when the research-contract receipt is missing
8. failure-closed behavior when required schema groups cannot be mapped safely
9. safe `tmp/**` output acceptance
10. protected or absolute output-path rejection
11. deterministic JSON ordering
12. `--strict` exits nonzero on blockers

## Not Yet Admitted

This packet does not yet admit:

- fixture filenames
- exact worker command strings
- implementation-readiness verdict
- worker execution
- marker movement to `10%`

Those belong to the next prompt-pack packet and later implementation packets.

## Marker Decision

No marker moves.

`Cortex Simulation Substrate Readiness` remains `0%`.

Reason:

- this packet admits only the future helper/test slice
- no requirements helper is implemented yet
- no requirements-map proof exists yet
- no separate marker-ratchet decision has been published

## Next

Open only this next packet:

```text
Cortex Simulation Substrate Readiness simulation requirements map prompt-pack and worker handoff contract
```

That packet may freeze the worker instructions, proof commands, fixture posture, and stop conditions, but it must still keep simulation execution, owner-repo mutation, secret-bearing input, deploy mutation, and marker movement denied.

## Validation

Validated during this admission pass:

- `python ops/validation/validate_stack.py` -> `critical=0 error=0`
- `python ops/atlas/marker_knockout_selector.py --format json`
- `python ops/atlas/marker_knockout_selector.py --format markdown`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python -m unittest tests.test_atlas_marker_knockout_selector -v`

## Completion

Completion: `100%` for the simulation requirements-map first-implementation admission itself.

No owner repo was mutated.
No platform surface was mutated.
No secret, deploy, workflow, or protected surface was touched.
