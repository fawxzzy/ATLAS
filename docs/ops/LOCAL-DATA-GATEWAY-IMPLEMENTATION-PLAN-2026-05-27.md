# Local Data Gateway Implementation Plan - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway initial implementation planning`
- Mode: `docs-only implementation plan`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-2026-05-25.md`
  - `docs/ops/CORE-PATTERN-CONVERGENCE-MATRIX-2026-05-24.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/atlas-book/10-failure-modes-and-recovery.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/atlas-book/14-lane-split-execution.md`
- Control-plane checkpoint: `main@eb3acf0`

## Objective

Turn `Local Data Gateway` from marker-only doctrine into a reusable initial implementation plan, without writing code yet.

This pass does not:

- implement `_stack` code
- implement Playbook code
- export raw data
- mutate Supabase, Vercel, Discord, runtime, schema, or app code
- open any approval-gated remote lane
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `eb3acf0`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=307`

## First Concrete Gateway Candidates Already Present In Stack Work

### Supabase export packets

Strongest current fit for first reusable gateway structure.

Why:

- already uses row-scope review, rollback posture, and approval packets
- already needs local redaction, minimization, provenance, and schema discipline
- already has a receipt chain where packet quality affects mutation safety

Initial gateway use:

- normalize local export rows into a consistent packet shape
- classify sensitivity before any sharing or model use
- produce a redacted review manifest plus a rollback map

### DiscordOS boundary receipts

Strong fit for non-data packet discipline.

Why:

- boundary receipts already carry precise scope and blocked-class reasoning
- they demonstrate packet minimization for architectural state, not just record data
- they are a good proving lane for provenance, schema/version, and transformation records

Initial gateway use:

- shape repo-local contract summaries into minimum useful handoff packets
- keep repo-local evidence separate from widened runtime or transport assumptions

### Vercel helper / dependency checks

Strong fit for local operational review packets.

Why:

- the helper-surface and stale-surface lanes repeatedly compress noisy platform state into reviewable decisions
- the same local preprocessing steps recur:
  - normalize
  - dedupe
  - classify
  - compress to decision-ready payload

Initial gateway use:

- turn raw platform listings into a minimal dependency-check packet
- preserve provenance and deletion risk classification

### Future AI / model prompt payload shaping

Strategic fit for later cross-stack reuse.

Why:

- prompt payloads are the easiest place for raw-data sprawl, secret leakage, duplicate state, and weak provenance
- the stack already has the doctrine but not yet a reusable local-first packet contract

Initial gateway use:

- require packet framing before model-facing payload assembly
- keep prompts downstream of local normalization and sensitivity classification

## Reusable Gateway Boundary

Every gateway packet should pass through the same local-first stages:

1. normalize
   - standardize shape, naming, and record boundaries
2. validate
   - fail closed on missing required fields or ambiguous source state
3. redact
   - remove secrets, private values, and non-purpose-bearing noise
4. classify sensitivity
   - label payload as public, internal, sensitive, or restricted
5. dedupe
   - collapse repeated rows, repeated log noise, or repeated receipt references
6. record provenance
   - identify owner surface, source files, source command, and capture time
7. stamp schema/version
   - make packet format explicit and evolvable
8. record transformation history
   - note the local reductions performed before export
9. enforce minimum useful payload
   - keep only fields necessary for the next remote or shared step

## Proposed Packet Contract

First reusable contract fields:

- `packet_purpose`
- `packet_schema_version`
- `sensitivity`
- `owner_surface`
- `source_provenance`
- `transformation_record`
- `dedupe_policy`
- `validation_status`
- `payload_summary`
- `payload`

Recommended supporting shape:

```yaml
packet_purpose: supabase-review | boundary-handoff | dependency-check | model-prompt-input
packet_schema_version: ldg.v1
sensitivity: public | internal | sensitive | restricted
owner_surface: repo-or-lane-owner
source_provenance:
  source_type: export | receipt-chain | command-output | local-file-set
  source_refs: []
  captured_at: iso8601
transformation_record:
  normalized: true
  validated: true
  redacted: true
  sensitivity_classified: true
  deduped: true
  notes: []
dedupe_policy: first-meaningful | merge-by-key | exact-drop
validation_status: pass | fail
payload_summary:
  record_count: 0
  dropped_fields: []
  retained_fields: []
payload: {}
```

## First Reusable Implementation Surfaces

### 1. Docs contract

First surface to land.

Why:

- lowest-risk place to freeze contract semantics before code
- gives `_stack`, Playbook, and owner repos one shared packet vocabulary

Recommended next artifact:

- `docs/contracts/local-data-gateway-packet-contract.md`

### 2. `_stack` helper candidate

Best first execution surface.

Why:

- gateway preprocessing is cross-stack and should not fork immediately into repo-specific scripts
- `_stack` already owns governed shared execution and validation-style helpers

Recommended first helper shape:

- `stack data gateway packet <lane>`

Expected responsibilities:

- accept local source inputs only
- enforce schema/version
- apply redaction and sensitivity labeling
- emit a packet plus a receipt-ready summary

Not in first helper scope:

- remote sync
- mutation
- deploy
- publication

### 3. Playbook doctrine candidate

Best first doctrine surface after the packet contract exists.

Why:

- the gateway is reusable governance, not just a one-off ATLAS note
- Playbook should eventually own the rule language for packet discipline

Recommended doctrine candidate:

- `playbook data packet doctrine`

Expected content:

- local-first packet rule
- minimum useful payload rule
- provenance and transformation-record requirement
- failure modes for raw prompt or raw export dumping

## First Candidate Workflows

### Workflow 1: Supabase review packet

Goal:

- transform local export rows into redacted, schema-bound review payloads plus rollback maps

Why first:

- highest existing proof that the pattern already matters operationally

### Workflow 2: Vercel dependency-check packet

Goal:

- compress raw project metadata into a deletion or retain decision packet

Why second:

- repeated operational pattern with clear minimization value

### Workflow 3: DiscordOS boundary handoff packet

Goal:

- summarize repo-local boundary state into a purpose-built handoff packet without widening runtime assumptions

Why third:

- proves the gateway applies to architecture packets, not only tabular data

### Workflow 4: Model prompt input packet

Goal:

- require local packet shaping before any future AI-facing payload leaves the machine

Why later:

- high leverage, but best adopted after the contract and helper semantics are stable

## Delivery Sequence

1. land this implementation plan
2. draft the docs contract
3. draft `_stack` helper contract and CLI shape
4. promote Playbook doctrine
5. only then implement `_stack` helper code
6. prove the helper first on a Supabase review packet

## Marker Recommendation

Keep `Local Data Gateway` at `0%` in this pass.

Why:

- this is still planning, not proof of reusable packet generation
- no helper, contract implementation, or packet receipt has been executed yet
- the marker should rise on doctrine-plus-proof, not on planning alone

## Exact Next Package

`Local Data Gateway packet contract draft`

Why:

- it is the smallest durable artifact between marker-only doctrine and code
- it freezes the packet vocabulary before helper implementation
- it reduces ambiguity for both `_stack` and Playbook follow-on work

## Rule

Local Data Gateway planning must stay local-first and payload-minimizing.

## Pattern

Raw local source -> gateway packet contract -> `_stack` packet helper -> owner-lane proof packet -> remote or shared consumer

## Failure Mode

Turning the gateway marker into vague doctrine without naming the first reusable implementation surfaces, packet contract fields, and proof workflows.
