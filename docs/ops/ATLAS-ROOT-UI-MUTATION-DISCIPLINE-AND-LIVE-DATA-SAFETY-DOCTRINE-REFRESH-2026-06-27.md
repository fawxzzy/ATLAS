# ATLAS Root UI Mutation Discipline And Live Data Safety Doctrine Refresh

Date: 2026-06-27

## Scope

- close the remaining root-governance residue around UI mutation proof discipline
- align ATLAS root rules, the visual workflow contract, and the QA LLEL standard on one checklist-backed proof posture
- harden live-data handling language for governed visual QA and mutation work without reopening product implementation lanes

## Executed

1. Updated `AGENTS.md` with explicit root rules for:
   - UI mutation checklist discipline
   - canonical-surface-first normalization
   - route-aware proof requirements
   - live user-data safety during visual QA and investigation
   - lane-switch behavior when one root lane blocks and another remains execution-ready
2. Updated `docs/architecture/VISUAL-CHANGE-WORKFLOW.md` so the visual loop now requires:
   - canonical surface identification before sibling normalization
   - requested-edit checklist creation before mutation
   - checklist reconciliation after capture
   - explicit data-lane labeling
   - at least one mobile lens when closing mobile-first Fitness UI work
3. Updated `docs/standards/ATLAS-QA-LLEL.md` so governed UI mutation evidence now requires:
   - requested-edit checklist reconciliation
   - canonical-surface-aware verification across normalized siblings
   - data-lane labeling for mutable product-data proof
   - report surfaces that show canonical target, checklist status, and QA-vs-live-data posture
4. Added this doctrine refresh receipt to the canonical receipt spine in `docs/atlas-book/05-receipt-index.md`.

## Findings

- the root governance surfaces now agree that a generally healthy route is not sufficient proof for a bounded UI edit batch
- the visual workflow and the QA LLEL now both require itemized requested-edit reconciliation instead of allowing `page loads` or generic screenshot success to stand in for actual mutation closeout
- canonical-surface-first normalization is now explicit doctrine rather than an implied review preference
- live-data safety is now part of the shared proof contract, not an ad hoc operator courtesy
- this pass is doctrine hardening only; it does not change marker posture, reopen protected QA blocker classes, or authorize new owner-repo mutation

## Validation

- verified path-discipline consistency by keeping the updated doctrine surfaces ATLAS-root-relative only
- re-ran `python ops/validation/validate_stack.py --ratchet`

Current validation result remains:

- `critical=0 error=0 warning=4 info=0`

The warning floor is still the inherited mutable-state residue class and was not widened by this doctrine refresh.

## Next Honest Move

- do not treat this doctrine packet as a marker ratchet by itself
- use the tightened checklist and live-data rules on the next actual governed UI mutation batch
- keep `docs/atlas-book/09-automation-and-command-candidates.md` outside this packet unless a later exact automation doctrine lane explicitly selects it
