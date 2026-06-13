# Marker Board Taxonomy Hygiene And Atlas Clean-Re-sync Campaign Pass 1 - 2026-06-13

- Date: `2026-06-13`
- Lane: `marker board taxonomy hygiene`
- Owner: `ATLAS/root`
- Mode: `root read-model cleanup and marker taxonomy tightening`
- Source surfaces:
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/FITNESS-PROTECTED-MARKER-CLOSEOUT-AFTER-QA-LLEL-CONTRACT-REFRESH-AND-LOCAL-BRANCH-WORKTREE-CLEANUP-2026-06-13.md`
  - `git rev-list --left-right --count origin/main...HEAD` at the ATLAS root
  - `python .\ops\validation\validate_stack.py --ratchet`
  - `python .\ops\atlas\marker_knockout_selector.py --format json`
  - `python .\ops\atlas\marker_knockout_selector.py --format markdown`

## Done

- cleaned the live marker board so open markers stay in open sections and closed ratchets stay in `Closed / Locked Ratchets`
- removed the duplicate `DiscordOS Runtime & Product Hardening` entry from `Supporting Open Markers`
- truncated `Closed / Locked Ratchets` to compact one-line `100%` entries
- grouped supporting open markers by active blocker cluster without breaking parser-compatible marker lines
- tightened restart guidance so the compact closed-ratchet rule is explicit outside the marker page itself

## Now

- `ATLAS origin/main` and local `HEAD` remain aligned at `a19bbbae1f7f8ef4f060b85f87b49bcca1794b2a`
- root validation is green at `critical=0 error=0 warning=58 info=0`
- the live marker board now reads as:
  - open front-page markers only
  - grouped supporting open markers only
  - compact closed ratchets only
- detailed closeout proof remains in receipts and the receipt index rather than inside the ratchet list

## Next

- keep the next root packet execution-facing instead of reopening another board-shape pass by default
- treat `AI Repetition-to-Automation Pipeline` as the current selector-admissible root marker while `AI Long-Run Batch Orchestration` remains the downstream active control-plane family it is feeding

## Marker Taxonomy Decisions

### Open front-page versus supporting open

- `Active Front-Page Marker Table` should carry open front-page markers only
- `Supporting Open Markers` should carry open non-front-page markers only
- closed ratchets should not remain duplicated in either open section

This is taxonomy cleanup, not marker movement.

### Closed ratchets

- keep the closed ratchet list parser-compatible as one-line `- Marker: \`100%\`` entries
- move detailed closeout evidence to receipts and `05-receipt-index.md`
- preserve `Materially Closed Carry-Forward Families` for restart-relevant held ladders that are not the same thing as simple closed ratchets

### Duplicate Surface Decommission

Decision: do not split into permanent submarkers yet.

Carry these as explicit unlock conditions instead:

- unique-state verification
- archive/delete or disposition authority

Reason:

- the blocker story is now clearer, but this pass did not clear either blocker class
- a new submarker would add open-board clutter without creating a new executable packet today

### Tmp Dependency Elimination

Decision: do not split into permanent submarkers yet.

Carry these as explicit unlock conditions instead:

- retained tmp disposition truth
- no-tmp-reentry proof

Reason:

- the blocker story is now clearer, but this pass did not clear either blocker class
- a new submarker would add open-board clutter without creating a new executable packet today

### Atlas Clean-Re-sync Campaign candidate

Decision: rejected for admission in this pass.

Why it was not admitted:

- this pass defines the candidate cleanly enough to discuss, but not cleanly enough to justify a new standing marker
- the candidate overlaps too heavily with existing truth already carried by `Full Stack Re-sync, Clean & Closeout: 100%`, `Workstation Resource Hygiene: 10%`, and the active root marker board itself
- today changed board taxonomy and restart readability, but did not create a distinct new proof threshold or stop condition that would stay stable as a separate campaign marker

If the candidate is ever admitted later, it should require all of:

- one explicit scope that is narrower than generic root cleanup
- one proof threshold that is not already carried by existing markers
- one stop condition that does not collapse back into another closeout or hygiene lane

## Marker Movement

- no marker percentage moved in this pass
- no closed ratchet was reopened
- no open marker was promoted or merged
- the change is board taxonomy only

## Validation

- `git fetch origin main`
- `git rev-list --left-right --count origin/main...HEAD`
  - result: `0	0`
- `git log -1 --oneline --decorate`
  - result: `a19bbbae (HEAD -> main, origin/main) docs: close fitness protected markers`
- `python .\ops\validation\validate_stack.py --ratchet`
  - result: `critical=0 error=0 warning=58 info=0`
- `python .\ops\atlas\marker_knockout_selector.py --format json`
  - result: parse succeeded; first admissible marker remains `AI Repetition-to-Automation Pipeline`
- `python .\ops\atlas\marker_knockout_selector.py --format markdown`
  - result: render succeeded

## Protected Surfaces Not Touched

- `archive/`
- `.vercel`
- `.env`
- `secrets/`
- deployment surfaces
- owner repos

## Local Residue Left Untouched

- existing unrelated edits in `docs/atlas-book/01-current-state.md`
- existing unrelated additional local edits in `docs/atlas-book/02-lanes-and-markers.md` outside this taxonomy pass
- untracked runtime-health receipts, screenshots, `.playwright-mcp/`, and other local residue already present in the root worktree

## Recommended Execution Path

- return to the active implementation lane rather than extending board cleanup by default
