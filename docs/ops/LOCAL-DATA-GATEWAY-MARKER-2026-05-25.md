# Local Data Gateway Marker

Date: 2026-05-25  
Mode: docs-only marker and doctrine package

## Marker Definition

`Local Data Gateway` tracks whether raw data is processed locally before it leaves the machine or repo boundary for a model, API, SaaS tool, remote database, automation, teammate, or shared system.

Starting marker:

- `Local Data Gateway: 0%`

## Rule

- raw data lands locally first
- remote systems receive purpose-built packets

## Pattern

`raw input -> local normalize/validate/redact/classify/dedupe/extract -> minimal schema'd payload -> remote refinement/sync/collaboration/specialized processing`

## 100% Completion Criteria

The marker reaches `100%` only when:

- raw data is local-by-default
- workflows normalize, validate, remove noise, redact sensitive values, classify sensitivity, dedupe repeated content, extract useful signal, and compress to the minimum useful payload before export
- every exported payload carries:
  - clear purpose
  - schema or version
  - sensitivity label
  - source or provenance
  - transformation record
  - minimum useful payload shape
- AI, model, API, SaaS, and remote database consumers receive refined packets rather than messy raw dumps
- Supabase, Vercel, Discord, and automation exports use governed gateway receipts
- repeated local preprocessing steps graduate into reusable `_stack`, Playbook, or bot command surfaces when stable enough
- sensitive values stop becoming accidental prompt, API, or shared-packet payloads

## Remote-System Doctrine

Remote systems should be treated as:

- refinement surfaces
- scale surfaces
- collaboration surfaces
- sync surfaces
- specialized processing surfaces

Remote systems should **not** be treated as:

- the first raw-data landing zone
- the place where noisy data gets cleaned up for the first time
- a substitute for local provenance, sensitivity labeling, or packet minimization

## Relationships To Existing Markers

### Operator Secret Path Hygiene

`Operator Secret Path Hygiene` protects where secrets live and how secret-backed flows avoid residue in repo roots.

`Local Data Gateway` complements it by ensuring raw data is redacted and sensitivity-labeled before it leaves local control.

### Fitness Supabase Profile/Data Hygiene

`Fitness Supabase Profile/Data Hygiene` governs one high-risk identity/data domain.

`Local Data Gateway` governs the cross-stack preprocessing discipline that should shape exports, approval packets, rollback manifests, and redacted review artifacts before any remote mutation or review.

### AI Repetition-to-Automation Pipeline

`AI Repetition-to-Automation Pipeline` tracks how repeated operator work becomes reusable command surfaces.

`Local Data Gateway` identifies one of the strongest repeated work families:

- normalize
- validate
- redact
- classify
- dedupe
- package minimum useful payload

### Core Pattern Convergence

`Core Pattern Convergence` measures whether strong reusable rules spread stack-wide.

`Local Data Gateway` should become one of those spread rules instead of staying isolated inside Supabase, secret, or export lanes.

### Playbook Everywhere + Cortex Interface

`Playbook Everywhere + Cortex Interface` makes doctrine visible and reusable.

`Local Data Gateway` gives that doctrine a concrete export-packet contract that Cortex, Playbook, `_stack`, and future bots can all read the same way.

### Truth Map & ATLAS Book

`Truth Map & ATLAS Book` records the durable operating model.

`Local Data Gateway` belongs there as first-class marker truth because it changes how the stack thinks about exports, remote collaboration, and automation boundaries.

## First Automation Candidates

Best first candidates:

1. `_stack` gateway packet scaffold
   - create a receipt-ready packet shell with purpose, schema or version, sensitivity, provenance, and transformation fields
2. local redaction and dedupe helper
   - package noisy rows or logs into a minimal review artifact before any remote handoff
3. Supabase export packet normalizer
   - convert row-review exports into governed redacted manifests plus rollback maps
4. Discord or Vercel update packet formatter
   - reshape local proof into minimum useful publication or review payloads without leaking raw operator noise

## Non-Goals

- no script implementation in this package
- no Supabase mutation
- no Vercel mutation
- no Discord posting
- no secret or env relocation
- no direct remote export from this packet
- no claim that all local processing should stay manual forever

## Marker Recommendation

- add `Local Data Gateway: 0%` as a first-class marker now
- treat future rises as doctrine-plus-proof progress, not as broad automation optimism

## Validation

Expected validation after this package:

- `python .\\ops\\validation\\validate_stack.py`
