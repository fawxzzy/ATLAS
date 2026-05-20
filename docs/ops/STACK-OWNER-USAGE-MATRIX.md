# Stack Owner Usage Matrix

This note is the root-owned reporting surface for how ATLAS currently depends on owner repos and adjacent guarded surfaces.

The matrix is evidence-backed from live repo/file reads. It does not create new owner truth. Each row is grounded in concrete stack-level surfaces such as imports, config refs, workflow/runtime calls, contract reads, proof/receipt consumption, or exclusion metadata that are visible from the ATLAS root and, where available, the live GitHub connector.

## Reading Rule

- Owner-lane priority should be based on live dependency evidence, not memory.
- Route by actual integration depth, not by which repo has been quiet.
- A concentrated active product rail can hide owner lanes; use this matrix to keep `_stack`, Playbook, Lifeline, Cortex, Fitness, and Verta explicit.

## Integration Depth Legend

- `deep`: root code or validators actively import, execute through, or block on the owner surface
- `medium`: root code or proof/config surfaces consume the owner surface directly, but not as a primary execution spine
- `light`: root references are real but mostly documentary, inventory, or planning reads
- `quarantined`: surface is intentionally visible only through exclusion, metadata, or trust-gate handling

## Matrix

| Owner Repo | Owner Role | Active Atlas Dependency Surfaces | Integration Depth | Trust Posture | Next Likely Lane |
| --- | --- | --- | --- | --- | --- |
| `_stack` | orchestration and merge/resume operator | Active dependency: `ops/atlas/run_session.py` bridges governed execution through `_stack` and records `_stack` as the `orchestrator_component`. Contract/read-model consumption: `ops/atlas/build_codex_context.py` pulls `_stack` runbooks, dispatcher protocol, orchestration docs, and `Invoke-CodexRepoTask.ps1` into the root context bundle. Validator/proof usage: `ops/cortex/supervise_workers.py` defaults to `_stack` worker-artifact examples for dry-run supervision. | `deep` | `trusted` in `stack.yaml` and `stack.lock.yaml`; active repo surface, but root treats it as orchestration owner rather than product truth | Keep `_stack` in the core operator lane for orchestration, merge, resume, and worker-handoff contract alignment |
| `playbook` | governance and verify owner | Active dependency: `ops/atlas/build_codex_context.py` and `ops/atlas/playbook_contract.py` read Playbook AGENTS, verify command docs, verify rules, and contract surfaces as owner-routing inputs. Contract/manifest consumption: `tests/test_atlas_playbook_contract_consumption.py` and `tests/test_atlas_playbook_verification_projection.py` project Playbook exports into root verification views. Planning/read-model usage: `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md` and `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md` consume Playbook contract exports as stack-visible evidence. Live repo refs: `fawxzzy/fawxzzy-playbook/AGENTS.md`, `README.md`, `docs/commands/README.md`, `packages/engine/src/docs/audit.ts`. | `deep` | `trusted`; active owner repo with root-visible contract exports | Keep Playbook in the active governance lane and route future owner priority by actual contract/workflow consumption rather than recent repo activity |
| `lifeline` | execution, approvals, and receipt owner | Active dependency: `ops/atlas/run_session.py` snapshots Lifeline as the `executor_component` and governs surfaces such as `runtime/lifeline/worker-execution`. Contract/read-model consumption: `ops/atlas/build_codex_context.py` reads Lifeline AGENTS, privileged-execution docs, and approval/request examples into the root context bundle. Validator/policy usage: stack docs and runbooks route privileged execution and proof-pass receipt semantics back to Lifeline contract docs, keeping root as coordinator instead of execution owner. Live repo refs: `fawxzzy/fawxzzy-lifeline/AGENTS.md`, `docs/privileged-execution.md`, `docs/contracts/privileged-execution-contract.md`, `scripts/test-privileged-execution-worker-bridge-deterministic.mjs`. | `deep` | `trusted`; active owner repo and active runtime owner for execution receipts | Keep Lifeline explicit in the core lane for approvals, receipts, and hermetic validation flow completion |
| `fitness` | application owner and current UI adoption rail | Validator/proof-only usage: `ops/atlas/ui_observe/fitness_capture_inputs.v1.json`, `ops/atlas/ui_observe/fitness_capture_map.v1.json`, and `ops/atlas/ui_visual_proof/fitness_visual_proof.v1.json` read Fitness truth-pack tokens/primitives plus concrete screen-family source refs. Root tests such as `tests/test_atlas_ui_observe.py`, `tests/test_atlas_ui_drift.py`, and `tests/test_atlas_ui_visual_proof.py` validate that root proof surfaces still point back to Fitness owner truth. Planning/read-model usage: `docs/ops/ATLAS-UI-OBSERVATION.md`, `docs/ops/ATLAS-UI-DRIFT-VALIDATION.md`, and `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md` treat Fitness as the active owner-proved UI lane. | `medium` | `trusted` for owner truth; root posture is validator/proof consumer only, not secondary UI truth owner | Keep the active product rail in Fitness: primitives first, harvest second, enforce third, adopt fourth |
| `stack` | root-owned subsystem (`Cortex`) | Active dependency: `stack.yaml` declares `subsystem_registry.cortex` with `owner: stack`, `role: read-only coordination runtime`, and `model: root-owned-subsystem`; `ops/validation/validate_stack.py` enforces that classification. Root code such as `ops/atlas/run_session.py`, `ops/atlas/awareness.py`, and `ops/cortex/*.py` reads and writes governed runtime artifacts under `runtime/cortex/**`. Validator usage: `ops/validation/validate_stack.py` keeps `repos/cortex` adjacent only and blocks child-repo drift. | `deep` | root-owned subsystem, `owner = stack`, `model = root-owned-subsystem`, active and read-only by doctrine | Keep Cortex in the validator/proof lane as root-owned coordination runtime; do not let `repos/cortex` drift back into active owner status |
| `foundation` | admitted control-plane repo | Topology and inventory dependency: `stack.yaml` admits `foundation` in `repo_registry`, `stack.lock.yaml` pins it as a managed component, and `ops/stack/export_repo_inventory.py` publishes it as part of the governed working set. Control-plane posture evidence: `repos/fawxzzy-foundation/README.md` presents Foundation as the active control-plane repo, while root validation already treats its local checkout as a normal managed repo path instead of a quarantined or trust-gated surface. Root does not currently execute through Foundation, but it does depend on Foundation being represented coherently in manifest, lock, and inventory truth. | `light` | `trusted`, `release_eligible = true`, admitted in governed topology | Keep Foundation admitted and align future control-plane usage through explicit root dependency evidence instead of local-checkout ambiguity |
| `Verta-Core` | quarantined adjacent historical surface | Quarantined reference usage: `stack.yaml` and `stack.lock.yaml` mark `repos/Verta-Core` and `repos/Verta-Core.zip` as excluded surfaces, untrusted, and non-release-eligible. `ops/validation/validate_stack.py` and `docs/ops/VERTA-TRUST-GATE.md` preserve the trust gate, while `docs/ops/VERTA-CORE-DEBT-ROUTING.md` keeps the backlog visible without admitting it into core-owner lanes. Tests such as `tests/test_atlas_codex_context.py` and `tests/test_atlas_continuity_manifest.py` verify visibility without reclassifying it as a core dependency. | `quarantined` | `untrusted`, `release_eligible = false`, metadata-only query posture | Keep Verta separate unless explicitly opened by new live evidence and an explicit trust decision; current lane is reference-only, not core dependency |

## Evidence Index

### `_stack`

- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/ops/atlas/run_session.py`
- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/ops/atlas/build_codex_context.py`
- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/ops/cortex/supervise_workers.py`
- Stack refs: `docs/registry/STACK-SYNERGY-REGISTRY.json`

### `playbook`

- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-playbook/blob/5abc4556031166feb2532c683d8dd7c8b6b09738/AGENTS.md`
- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-playbook/blob/5abc4556031166feb2532c683d8dd7c8b6b09738/README.md`
- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-playbook/blob/5abc4556031166feb2532c683d8dd7c8b6b09738/docs/commands/README.md`
- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-playbook/blob/5abc4556031166feb2532c683d8dd7c8b6b09738/packages/engine/src/docs/audit.ts`
- Root refs: `ops/atlas/build_codex_context.py`, `ops/atlas/playbook_contract.py`, `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`, `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`

### `lifeline`

- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-lifeline/blob/91f84332e5616a0e78982102df10fd678956211c/AGENTS.md`
- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-lifeline/blob/91f84332e5616a0e78982102df10fd678956211c/docs/privileged-execution.md`
- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-lifeline/blob/91f84332e5616a0e78982102df10fd678956211c/docs/contracts/privileged-execution-contract.md`
- Live GitHub refs: `https://github.com/fawxzzy/fawxzzy-lifeline/blob/91f84332e5616a0e78982102df10fd678956211c/scripts/test-privileged-execution-worker-bridge-deterministic.mjs`
- Root refs: `ops/atlas/run_session.py`, `ops/atlas/build_codex_context.py`, `docs/ops/ATLAS-LIFELINE-PLATFORM-RESTART.md`, `docs/ops/ATLAS-SESSION-RUNBOOK.md`

### `fitness`

- Root refs: `ops/atlas/ui_observe/fitness_capture_inputs.v1.json`
- Root refs: `ops/atlas/ui_observe/fitness_capture_map.v1.json`
- Root refs: `ops/atlas/ui_visual_proof/fitness_visual_proof.v1.json`
- Root refs: `tests/test_atlas_ui_observe.py`, `tests/test_atlas_ui_drift.py`, `tests/test_atlas_ui_visual_proof.py`
- Root refs: `docs/ops/ATLAS-UI-OBSERVATION.md`, `docs/ops/ATLAS-UI-VISUAL-PROOF.md`

### `Cortex`

- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/stack.yaml`
- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/ops/validation/validate_stack.py`
- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/ops/atlas/run_session.py`
- Root refs: `runtime/cortex/**`, `ops/atlas/awareness.py`, `ops/cortex/build_worker_context.py`, `ops/cortex/supervise_workers.py`

### `Verta-Core`

- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/docs/ops/VERTA-CORE-DEBT-ROUTING.md`
- Live GitHub refs: `https://github.com/fawxzzy/ATLAS/blob/719c45d813f1c32fe8c493a1a65fa39abd1d9d3d/docs/ops/VERTA-TRUST-GATE.md`
- Root refs: `stack.yaml`, `stack.lock.yaml`, `ops/validation/validate_stack.py`, `docs/knowledge/reviews/verta-core.md`, `tests/test_atlas_codex_context.py`

## Classification Notes

- `fitness` is an active owner dependency for proof and validation, but root still consumes Fitness as owner truth instead of storing a second UI truth model.
- `Cortex` is not a child repo dependency. It is a root-owned subsystem under `runtime/cortex/**`, and any `repos/cortex` checkout remains adjacent context only.
- `foundation` is admitted in root topology because the manifest, lock, and inventory pipeline can represent it coherently as a managed control-plane repo without widening execution authority.
- `Verta-Core` is intentionally visible so the stack can keep trust posture explicit. That visibility is not evidence of core-lane dependency.

## Failure Mode

The main failure mode is forgetting owner lanes because the active product rail is concentrated in one repo. When that happens, owner priority starts drifting toward memory or recency instead of live dependency evidence. This matrix is meant to stop that drift.
