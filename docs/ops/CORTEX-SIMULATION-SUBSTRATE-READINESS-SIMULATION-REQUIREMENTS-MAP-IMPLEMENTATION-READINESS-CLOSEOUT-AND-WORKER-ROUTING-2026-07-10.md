# Cortex Simulation Substrate Readiness simulation requirements map implementation-readiness closeout and worker routing

- Date: `2026-07-10`
- Lane: `Cortex Simulation Substrate Readiness`
- Mode: `ATLAS-root docs-only implementation-readiness closeout and worker routing`
- Scope: `decide whether the simulation requirements-map chain is explicit enough to route one bounded implementation worker without implementing the helper in this packet`
- Control-plane checkpoint: `main@3e8bbee2`
- Marker movement: none

## Why This Packet Exists

The Simulation lane now has:

- durable operator reselection
- durable research interpretation
- durable first-implementation admission
- durable prompt-pack and worker handoff

This packet closes the remaining root-only control-plane question:

- is the helper contract explicit enough to route one implementation worker safely

## Durability Check

The governing receipt chain is durable:

1. `docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md`
2. `docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-SIMULATION-SUBSTRATE-2026-07-09.md`
3. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md`
4. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
5. `docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md`

## Readiness Answers

### 1. Are the research contract, admission, and prompt-pack durable

Yes.

They are committed on `main`, receipt-indexed, and validation-clean.

### 2. Is the worker objective explicit

Yes.

The worker objective is to build one root-owned, read-only requirements mapper that emits deterministic advisory JSON and preserves every denied authority.

### 3. Are the exact worker and test files explicit

Yes.

The exact files are:

- `ops/cortex/simulation_substrate_requirements.py`
- `tests/test_cortex_simulation_substrate_requirements.py`

### 4. Is the CLI explicit

Yes.

The routed worker must implement:

```text
python ops/cortex/simulation_substrate_requirements.py --json --source <root-relative-path> --source <root-relative-path> --output <root-relative-path> --strict
```

### 5. Is the JSON schema explicit

Yes.

The required top-level fields, per-requirement fields, status model, safe-output posture, and deterministic-ordering expectation are frozen by the prompt-pack.

### 6. Are source boundaries explicit

Yes.

Allowed sources are root-owned receipts, architecture, doctrine, workflow-profile context, and safe fixtures only.

Owner repos, hidden transcripts, live product data, secret-bearing surfaces, network inputs, and generated media remain unadmitted.

### 7. Are path guards explicit

Yes.

The routed worker must reject:

- absolute paths
- paths outside the ATLAS root
- owner-repo roots
- `.env*`
- `.vercel`
- `.playwright-mcp`
- `archive/**`
- secret-bearing or protected paths

and may write only to explicit safe `tmp/**.json` outputs.

### 8. Are authority denials explicit

Yes.

The worker remains denied from:

- owner-repo mutation
- Vercel or Supabase mutation
- deploys
- workflow edits or dispatch
- secret handling
- final receipt emission
- marker movement
- `_stack` dispatch
- simulation execution
- model training

### 9. Are ethical, IP, and privacy boundaries explicit

Yes.

The worker must keep:

- unauthorized IP generation
- media generation
- impersonation
- hidden-data ingestion
- privacy leaks
- secret leaks
- authority creep

out of scope and visible as explicit risk classes.

### 10. Is the proof matrix sufficient

Yes.

The prompt-pack proof matrix covers:

- admitted-source acceptance
- forbidden-source rejection
- taxonomy coverage
- deterministic JSON behavior
- strict-mode exit behavior
- safe output-path rules
- authority-denial persistence
- warning-budget non-regression

### 11. Does any root-side ambiguity remain

No blocking root-side ambiguity remains.

Future ambiguity can still arise during implementation, but the control-plane contract is explicit enough to route one worker packet now.

### 12. Is implementation ready

Yes.

Readiness verdict:

- `implementation_ready`

### 13. What exact worker packet is routed

The exact worker packet is:

```text
Cortex Simulation Substrate Readiness simulation requirements map first-implementation worker packet 1
```

### 14. What exact files may the worker touch

The worker may touch only:

- `ops/cortex/simulation_substrate_requirements.py`
- `tests/test_cortex_simulation_substrate_requirements.py`

It may also write proof output only to explicit safe `tmp/**.json` paths during execution.

### 15. What reconciliation packet follows

The exact reconciliation packet is:

```text
Cortex Simulation Substrate Readiness simulation requirements map first-implementation worker cluster reconciliation
```

### 16. Does any marker move

No.

`Cortex Simulation Substrate Readiness` remains `0%`.

Research, admission, prompt-pack, and readiness routing do not satisfy the first implementation ratchet.

## Allowed Worker Scope

The routed worker may:

- implement the admitted helper
- implement focused tests for the frozen proof matrix
- read only admitted root-owned sources
- write proof outputs only to explicit safe `tmp/**.json` paths

The routed worker may not:

- mutate owner repos
- inspect hidden transcript state
- consume live Vercel or Supabase data
- widen the CLI beyond the frozen first contract
- claim an adapter exists
- run a simulation
- move markers

## Warning Budget Posture

The inherited validation warning baseline remains:

- warning count: `5`
- category set: `atlas-root-path` only
- debt class: `path-discipline-leaks`

The routed worker must preserve that ceiling unless a separately authorized debt-repair packet changes it.

The current rerun during this readiness pass reported `warning=0`.

This receipt does not claim a warning-burn closeout from Simulation work.

It records only that:

- the inherited baseline was not exceeded
- no new warning class appeared
- the current validation surface is cleaner than the inherited floor

## Worker-Routing Decision

Route exactly one future worker packet for:

- `ops/cortex/simulation_substrate_requirements.py`
- `tests/test_cortex_simulation_substrate_requirements.py`

No additional helper family is routed.

No selector rewrite is required.

No continuity manifest is required for this `0%` supporting marker packet chain.

## Exact Next Packet

The next exact packet is:

```text
Cortex Simulation Substrate Readiness simulation requirements map first-implementation worker packet 1
```

## Follow-On Reconciliation

After the worker lands, reconcile only through:

```text
Cortex Simulation Substrate Readiness simulation requirements map first-implementation worker cluster reconciliation
```

No marker ratchet packet is implied automatically.

## Marker Decision

No marker moves.

`Cortex Simulation Substrate Readiness` remains `0%`.

Reason:

- readiness routing is not implementation proof
- no helper or tests are landed by this receipt
- no simulation requirements map has been proven on canonical `main`

## Validation

Validated during this readiness pass:

- `python ops/validation/validate_stack.py` -> `critical=0 error=0 warning=0 info=0`
- `python ops/atlas/marker_knockout_selector.py --format json`
- `python ops/atlas/marker_knockout_selector.py --format markdown`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python -m unittest tests.test_atlas_marker_knockout_selector -v`

## Completion

Completion: `100%` for the implementation-readiness closeout and worker routing itself.

No owner repo was mutated.
No platform surface was mutated.
No secret, deploy, workflow, or protected surface was touched.
