# _Stack Readiness Stack Update Draft Report-Contract And Contradiction-Routing Pass 49 - 2026-06-08

- Date: `2026-06-08`
- Lane: `_stack Readiness stack update draft report-contract and contradiction-routing pass 49`
- Mode: `docs-only root-bounded report-contract design`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/ops/_STACK-READINESS-STACK-UPDATE-DRAFT-COMMAND-DESIGN-PASS-47-2026-06-08.md`
  - `docs/ops/_STACK-READINESS-STACK-UPDATE-DRAFT-EVIDENCE-ADMISSION-AND-PROOF-LEDGER-DISCIPLINE-PASS-48-2026-06-08.md`
  - `docs/ops/_STACK-READINESS-STACK-RECEIPT-PACKAGE-REPORT-CONTRACT-AND-CONTRADICTION-ROUTING-PASS-35-2026-06-04.md`
  - `docs/ops/UNIFIED-RELEASE-DEPLOY-UPDATE-HANDOFF-2026-05-24.md`
  - `docs/ops/MANUAL-DEPLOY-EXCEPTION-INVENTORY-2026-05-24.md`
  - `docs/atlas-book/07-contracts-and-seams.md`
  - `docs/atlas-book/08-workflow-recipes.md`
  - `docs/atlas-book/09-automation-and-command-candidates.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
- Control-plane checkpoint: `main`

## Objective

Freeze one compact authoritative report contract for `_stack` `stack update draft <repo>` and one explicit contradiction-routing rule.

This pass does not:

- implement the command
- mutate `repos/_stack`
- reopen pass-47 command design or pass-48 evidence discipline
- widen into publication execution, final wording generation, or owner proof creation
- claim that update-draft packaging execution is implementation-ready

## Inherited Result

Pass 47 already froze:

- the exact command purpose
- exact bounded inputs and outputs
- exact non-health failure exits
- the exact no-proof-creation/no-publication guard
- the exact package-basis rule

Pass 48 already froze:

- the exact admitted repo class as Fitness-only today
- one exact admitted owner proof basis
- one exact admitted owner ledger basis
- one optional same-story receipt-context ceiling
- fail-closed contradiction handling for proof, ledger, and off-story basis drift

This pass consumes those seams and freezes how the report must present that already-governed package posture.

## Exact Required Success Report Fields

Every successful update-draft report must emit:

1. `command`
   - fixed identifier: `stack update draft`

2. `repo`
   - one exact admitted repo identity

3. `package_mode`
   - exactly one of:
     - `package-ready`
     - `package-ready-plus-context`

4. `package_status`
   - fixed value:
     - `downstream-consumption-only`

5. `proof_ref`
   - one exact cited owner proof basis path or durable proof ref

6. `ledger_ref`
   - one exact cited owner ledger basis path or durable ledger ref

7. `package_fields`
   - one exact bounded structure summary naming:
     - repo identity
     - proof and ledger refs
     - deployment metadata slots already present in proof basis
     - shipped-evidence or release-note slots already present in ledger basis
     - downstream-consumption-only label

8. `context_status`
   - exactly one of:
     - `not-requested`
     - `agreed`
     - `ignored-as-inadmissible`

9. `routing_note`
   - one exact next routing posture only

## Exact Optional Success Report Fields

These fields may appear only when their condition is true:

1. `receipt_context`
   - only when `--receipt-context <relative-path>` was supplied
   - must echo the bounded relative path only

2. `deployment_metadata`
   - only when exact deployment metadata is already present in the cited proof basis

3. `ledger_notes`
   - only when exact shipped-evidence, release-note, or release-ledger narration is already present in the cited ledger basis

4. `context_note`
   - only when `context_status=agreed`
   - limited to one same-story deployment-context or blocked-state statement already present in the cited receipt

5. `context_fallback_reason`
   - only when `context_status=ignored-as-inadmissible`
   - must be one exact bounded reason rather than narrative smoothing

6. `contradiction_note`
   - only when `context_status=ignored-as-inadmissible`
   - limited to one bounded contradiction payload defined below

## Exact Failure Report Fields

When the command fails before a package may be emitted, it must emit:

1. `command`
   - fixed identifier: `stack update draft`

2. `failure_code`
   - one of:
     - `invalid-input`
     - `repo-unadmitted`
     - `proof-missing`
     - `ledger-missing`
     - `proof-ledger-contradiction`
     - `package-basis-unavailable`

3. `failure_scope`
   - exactly one of:
     - `input`
     - `repo-target`
     - `proof-basis`
     - `ledger-basis`
     - `proof-ledger-story`
     - `package-basis`

4. `message`
   - one bounded sentence only

5. `routing_note`
   - one exact next routing posture only

## Exact Conditional Success Payload

### `receipt-context ignored`

May include:

- `receipt_context`
- `context_status=ignored-as-inadmissible`
- `context_fallback_reason`

May also include one bounded `contradiction_note` containing:

- `contradiction_scope`
  - `receipt-context`

- `conflicting_refs`
  - flat list only

- `summary_consequence`
  - `package-ready-without-context`

only when:

- the cited proof basis and cited ledger basis are still sufficient and non-contradictory
- the contradiction is limited to the optional same-story receipt context
- the command drops the receipt context instead of fabricating aligned wording

No other success mode may emit a contradiction payload.

## Exact Conditional Failure Payload

### `proof-ledger-contradiction`

May include one bounded `contradiction_note` containing:

- `contradiction_scope`
  - `release-story`
  - `production-posture`
  - `commit-or-target`
  - `shipped-versus-blocked-posture`

- `conflicting_refs`
  - flat list only

- `summary_consequence`
  - `no-package`

No other failure code may emit a contradiction payload.

## Exact Text Report Contract

### `package-ready`

Text output must contain, in this order:

1. one exact package-status line
2. one exact repo line
3. one exact basis line naming `proof_ref` and `ledger_ref`
4. one exact structure-summary line or block
5. one routing line

### `package-ready-plus-context`

Text output must contain, in this order:

1. one exact package-status line
2. one exact repo line
3. one exact basis line naming `proof_ref` and `ledger_ref`
4. one exact structure-summary line or block
5. one exact context line or block
   - limited to exact proof-backed deployment metadata already admitted
   - exact ledger-backed shipped-evidence notes already admitted
   - and one exact same-story receipt-context statement only when admitted
6. one routing line

### `failure`

Text failure output must contain only:

1. `failure_code=<code>`
2. one bounded message line
3. one routing line

and may include the bounded contradiction payload only when admitted above.

## Exact JSON Report Contract

### `success`

JSON success output must contain:

- `command`
- `repo`
- `package_mode`
- `package_status`
- `proof_ref`
- `ledger_ref`
- `package_fields`
- `context_status`
- `routing_note`

and only the conditionally admitted optional fields.

### `failure`

JSON failure output must contain:

- `command`
- `failure_code`
- `failure_scope`
- `message`
- `routing_note`

and only the conditionally admitted contradiction payload.

## Exact Forbidden Report Fields

The report may not emit:

- final Discord copy
- publication approval
- deploy approval
- proof-creation claims
- owner-readiness claims beyond the cited proof and ledger surfaces
- multiple competing routing recommendations
- contradiction narration without cited refs
- receipt-context wording after that receipt has been rejected as inadmissible
- prose that smooths a dropped receipt context into implied certainty

## Exact Routing Note By Outcome

### `package-ready`

Routing note must say only:

- `package downstream-consumption only from exact proof and ledger basis`

### `package-ready-plus-context`

Routing note must say only:

- `package downstream-consumption only from exact proof and ledger basis plus one same-story context`

### `receipt-context ignored`

Routing note must say only:

- `package downstream-consumption only from exact proof and ledger basis and ignore inadmissible receipt context`

### `invalid-input`

Routing note must say only:

- `fix invocation and rerun before packaging`

### `repo-unadmitted`

Routing note must say only:

- `keep helper scoped to the admitted Fitness release-to-update class`

### `proof-missing`

Routing note must say only:

- `cite one exact admitted owner proof basis before packaging`

### `ledger-missing`

Routing note must say only:

- `cite one exact admitted owner ledger basis before packaging`

### `proof-ledger-contradiction`

Routing note must say only:

- `reconcile owner proof and ledger truth before packaging`

### `package-basis-unavailable`

Routing note must say only:

- `restore one exact same-story proof-plus-ledger basis before packaging`

## Exact Contradiction Rule

### Proof-ledger contradiction

Counts as proof-ledger contradiction when:

- the cited proof basis and ledger basis disagree on one release story identity
- they disagree on production versus preview posture
- they disagree on commit, deployment target, or release target identity
- or they disagree materially on shipped versus blocked posture

Output:

- `failure_code=proof-ledger-contradiction`
- no package payload

Routing:

- reconcile owner proof and owner ledger truth before packaging

### Receipt-context contradiction

Counts as cited-receipt contradiction when:

- the cited receipt conflicts with the cited proof basis or cited ledger basis
- the cited receipt belongs to an older superseded release story
- or the cited receipt attempts to stand in for missing owner proof or missing owner ledger truth

Output:

- success may continue only as `package-ready`
- `context_status=ignored-as-inadmissible`
- no context note may be emitted

Routing:

- ignore the receipt context unless one later bounded same-story cleanup packet is still truly needed

## Exact Root-Side Follow-On Packet Rule For Contradictions

When contradiction is limited to one optional same-story receipt:

- root should not open a fake proof-or-ledger reconciliation packet by default
- root may open one bounded same-story receipt cleanup packet only if downstream wording still truly needs that dropped context

When contradiction touches the cited proof basis or ledger basis:

- root must not open implementation-admission or execution packets from that broken package basis
- root must route to the owner-side proof or ledger surface that owns the missing truth

## Exact Out-Of-Scope Boundary

Still out of scope:

- implementation admission
- live command execution
- repo mutation
- publication execution
- final wording generation
- proof-matrix admission
- broader repo-class widening beyond current Fitness-only truth

## Exact Next Package

`_stack Readiness stack update draft implementation-admission and no-execution guard pass 50`

Why:

- command purpose, evidence rules, report shape, receipt-context drop behavior, and contradiction routing are now frozen
- the next remaining docs-only ambiguity is the exact implementation-admission line without letting report-contract work imply live execution or publication permission

## Recommendation Type

`durable with bounded inference`

Durable because:

- this pass closes the last report-shape ambiguity left open by passes 47 and 48
- the optional receipt-context exception stays bounded to the already-frozen proof-ledger hierarchy

Bounded inference because:

- pass 50 is compressed from the remaining implementation-admission ambiguity by analogy to the earlier `_stack` command families

## Ratchet Decision

Ratchet:

- `none`

Why:

- this pass freezes one required operator-facing report seam for the admitted fourth-family support surface
- `_stack Readiness` already sits at `99%`, and no implementation slice, governed operator proof, or broader execution closure landed that would honestly justify `100%`

## Validation Note

The inherited root-validation snapshot for the current merged working state remains:

- `critical=0 error=0 warning=43 info=0`

This pass does not claim a fresh full rerun of `python .\ops\validation\validate_stack.py --ratchet`, because that command remains unresolved in-session.

## Rule

`Package Ready Must Stay Narrower Than Publication`

If proof and ledger truth are sufficient, package only the bounded downstream-consumption payload; do not let report polish make the helper sound like publication approval, final copy generation, or owner-truth replacement.

## Pattern

`Exact Proof Plus Ledger Package, Optional Same-Story Context`

admitted repo -> one exact owner proof basis -> one exact owner ledger basis -> optional same-story receipt context -> drop inadmissible optional context -> fail closed on proof-ledger contradiction

## Failure Mode

`Polished Update Overclaim`

If the report contract lets optional context drift or contradiction collapse into polished prose, the helper sounds more certain and more publication-ready than the admitted owner proof and ledger surfaces actually are.
