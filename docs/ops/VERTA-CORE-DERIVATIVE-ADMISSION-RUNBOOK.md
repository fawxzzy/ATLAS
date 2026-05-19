# Verta-Core Derivative Admission Runbook

## Purpose

Execute Verta-Core absorption as a derivative-admission and contract-first migration that preserves ATLAS path policy, repo ownership, and trust controls.

Use this runbook only for stack-level planning, intake, and cross-repo coordination. Repo-local implementation still belongs in the owning repo.

## Guardrails

- Do not edit `repos/Verta-Core/**` from a root session unless a separate explicit scrub lane is opened.
- Do not treat imported Verta material as trusted just because it resembles existing Verta history.
- Keep runtime state in `runtime/`, disposable outputs in `tmp/`, durable imports in `data/`, and stack doctrine in `docs/`.
- Use relative ATLAS paths in every new artifact.
- Prefer an existing owner repo or delivery lane over inventing a new one.

## Phase -1: Topology Coherence Preflight

Objective:

- make sure the first owner-surface registration is anchored to trustworthy stack metadata

Actions:

- compare `stack.yaml`, `stack.lock.yaml`, `docs/registry/STACK-REPO-INVENTORY.json`, `README-STACK.md`, and `docs/ops/STACK-OWNER-USAGE-MATRIX.md`
- confirm participating repo ids and excluded surfaces agree closely enough for ownership routing
- confirm Verta-Core is still quarantined and non-release in every relevant surface
- record any drift that must be resolved before derivative registration

Exit gate:

- topology is coherent enough to name an owner surface without ambiguity

Phase `-1` completion note:

- Rule: Verta-Core absorption admits derivatives, never the raw archive or raw checkout.
- Pattern: ATLAS root owns topology, contracts, doctrine, and projection; owner repos own executable behavior.
- Failure mode: admitting a Verta-derived seam against drifting topology creates false certainty and can route ownership to the wrong repo.
- Link the current coherence evidence to `runtime/receipts/validation/stack-validation.latest.md` and `runtime/receipts/validation/stack-validation.latest.json`.
- Phase 0 cannot begin until `stack.yaml`, `stack.lock.yaml`, the published inventory, `README-STACK.md`, and `docs/ops/STACK-OWNER-USAGE-MATRIX.md` agree on governed repos, deferred adjacent surfaces, and the standing Verta quarantine posture.

## Phase 0: Intake And Quarantine

Objective:

- make the source safe to inspect without silently promoting it

Actions:

- place raw zips, bundles, or copied trees under `data/imports/knowledge/<scope>/verta-core/raw/`
- extract into `data/imports/knowledge/<scope>/verta-core/extracted/`
- record provenance, checksum, and source notes in the intake manifest
- review for secrets, local path leakage, executable residue, vendor installers, and auth material
- write scrub findings under `docs/knowledge/reviews/`
- keep the surface metadata-only if trust is unresolved

Exit gate:

- raw evidence preserved
- no imported code executed
- risk posture documented
- initial artifact families classified

## Phase 1: Classification And Ownership Freeze

Objective:

- decide what Verta-derived behavior is worth admitting and where it belongs

Actions:

- classify each artifact family as one of:
  - application
  - governance-runtime
  - local-operator
  - workflow-operator
  - archive
  - quarantined
- choose the participating repo ids
- decide whether any slice requires a new admitted owner repo
- choose one concrete derivative owner surface as the first admission target
- draft the owner-facing seam list for:
  - health
  - event emission
  - receipt emission
  - environment shape
  - deployment lane
- draft a repo-owned `atlas.app-registration.v1` before promotion

Exit gate:

- repo class is explicit
- participating repos are named
- one derivative owner surface is named explicitly
- contract seams are frozen enough to implement adapters

Current Phase 0 selection:

- owner repo: `playbook`
- derivative seam: `verta-derivative-pattern-pack`
- owner artifact: `repos/fawxzzy-playbook/docs/contracts/VERTA_DERIVATIVE_PATTERN_PACK.md`
- source provenance: reviewed derivative notes only; raw `Verta-Core` evidence remains quarantined

Phase 0 exit criteria for this seam:

- Playbook-owned derivative contract note exists
- proposed `atlas.app-registration.v1` shape is documented
- the Playbook derivative artifact is reviewed and promotion-ready, with explicit provenance, trust boundary, review state, and deterministic promotion criteria
- Playbook verify and docs audit pass
- ATLAS ratchet is not red because of topology or unrelated recovery-surface leaks
- any later adapter/parity lane is justified by a new explicitly selected executable seam, not assumed from this governance seam

Phase 0 completion note for the current seam:

- Rule: Verta-Core derivatives can be promoted only after they are rewritten as owner-repo artifacts with explicit provenance, trust boundary, and verification evidence.
- Pattern: The first safe absorption surface is a Playbook pattern pack because governance and architecture knowledge can be reviewed without granting runtime authority.
- Failure mode: jumping from Verta-derived ideas directly into Lifeline, `_stack`, or app runtime behavior skips the proof layer and risks converting untrusted historical material into executable stack behavior.
- Adapter, parity, and cutover work remain blocked until this reviewed derivative artifact exists and a later executable seam is named explicitly.

## Phase 2: Adapter Lane

Objective:

- make the legacy surface visible through ATLAS-compatible seams without removing legacy authority yet

Actions:

- add a health adapter that produces `atlas.health.v1`
- add an event envelope adapter for platform-visible events
- add receipt emission for migration actions and verification steps
- extract hardcoded config into environment variables
- introduce route, job, or deploy adapters instead of rewriting the full legacy surface
- keep the legacy path authoritative during this phase

Exit gate:

- contract tests pass at the seam
- no cutover of system-of-record authority yet
- rollback remains trivial because adapters can be disabled

## Phase 3: Parity And Verification

Objective:

- prove the new path is equivalent enough to cut over safely

Actions:

- run owner-repo `verify` or `verify:strict`
- validate `packages/atlas-contracts`
- compare legacy and target data with counts, hashes, or invariant checks
- run migration-chain validation where schema history matters
- smoke test the runtime path and key user flows
- rehearse rollback before traffic or authority moves

Commands:

```powershell
node packages/atlas-contracts/scripts/validate-contracts.mjs
python .\ops\validation\validate_stack.py --ratchet
```

Exit gate:

- contract validation green
- stack validation green in ratchet mode
- repo-local verification green for the participating owner repos
- parity drift understood or resolved
- rollback rehearsal documented

## Phase 4: Cutover

Objective:

- move authority to the ATLAS-aligned owner surface with a bounded rollback window

Actions:

- shift traffic or scheduled execution progressively
- switch system-of-record authority only after parity gates are green
- record release activation and rollback references in the owner lane
- keep the old route, manifest, or credentials available for the rollback window
- watch health, receipts, and error posture during the soak period

Exit gate:

- target path is authoritative
- soak window completes without unresolved critical regressions
- rollback window closes by explicit decision, not assumption

## Phase 5: Stabilization And Archive

Objective:

- preserve lineage while removing dead paths from the active operating lane

Actions:

- archive superseded scripts, manifests, and notes into the correct historical lane
- update root-owned registry or inventory notes if the repo set changed
- keep receipts, parity reports, and cutover notes discoverable
- remove only the legacy surfaces that are proven dead

Exit gate:

- active owner surface is clear
- historical evidence remains attributable
- no active docs point operators back at retired legacy paths

## Acceptance Checklist

- identity and provenance are explicit
- any link to `Verta-Core` is either proven or kept separate
- the first admitted surface is a derivative owner surface, not the raw Verta checkout
- repo class is explicit
- owner repo routing is explicit
- deployment lane is explicit
- `atlas.app-registration.v1` exists or is approved for the owner surface
- health, event, and receipt seams are defined
- secrets were extracted and any exposed values were rotated
- parity evidence exists for system-of-record data
- rollback was rehearsed before final cutover
- root validation and owner-repo validation both passed

## Operator Notes

- Root sessions should create doctrine, checklists, and coordination artifacts.
- Owner-repo sessions should implement adapters, parity tooling, and cutover behavior.
- If the work starts drifting toward broad cleanup inside an untrusted historical checkout, stop and reopen the routing decision explicitly.
