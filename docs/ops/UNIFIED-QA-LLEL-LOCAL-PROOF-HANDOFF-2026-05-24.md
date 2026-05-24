# Unified QA / LLEL / Local Proof Handoff

Date: 2026-05-24
Lane: Unified Workflow Convergence
Mode: docs-only handoff map
Status: proof handoff baseline recorded

## Goal

Define one canonical proof workflow that connects automated QA/LLEL checks, local desktop and mobile server proof, browser and manual review, release-readiness evidence, Discord feedback-card closeout, ATLAS root receipt packaging, and Playbook doctrine extraction.

This pass does not deploy, post to Discord, mutate app code, mutate Vercel, mutate Supabase, or reopen paused preview/deploy lanes.

## Governing Rules

- Repo-owned QA blockers must be fixed in the owning repo, not hidden in root logic.
- Proof must exist before release, deploy, or Discord publish boundaries advance.
- `tmp` is never a source-of-truth fallback.
- Manual attestation may satisfy physical/manual review, but it must not be labeled as automated proof.
- Discord feedback is a bounded evidence intake surface, not engineering truth by itself.
- ATLAS root records cross-repo proof posture; it does not replace repo-owned proof artifacts.

## Canonical Proof Chain

1. Automated QA/LLEL boundary
2. Local desktop server boundary
3. Mobile LAN and device proof boundary
4. Browser/manual/plugin proof boundary
5. Release-readiness evidence boundary
6. Feedback-card closeout boundary
7. Discord update proof dependency
8. ATLAS root receipt packaging boundary
9. Playbook doctrine extraction

## Boundary Map

| Stage | Canonical entrypoint | Owner | Required proof before handoff | Output |
| --- | --- | --- | --- | --- |
| Automated QA/LLEL | repo-local QA/LLEL commands and harnesses | owner repo | deterministic test and capture receipts | machine-readable proof baseline |
| Local desktop server | repo-local dev/preview loop | owner repo | local server reachable and correct env/path boundary | live local app surface |
| Mobile LAN and device proof | repo-local mobile/LAN loop and manual device checks | owner repo | authenticated local route proof and fresh captures | mobile/UI confidence |
| Browser/manual/plugin proof | browser automation, manual spot checks, plugin captures | owner repo with operator assist | live route renders and capture evidence | reviewed visual/runtime proof |
| Release readiness | repo-owned release-readiness commands/docs | owner repo | verify/build/mobile/QA evidence complete | release-ready candidate |
| Feedback closeout | feedback export, completion review, card status flow | owner repo + planning surfaces | shipped work linked back to reviewed card | closed-loop feedback evidence |
| Discord update dependency | repo-owned update draft/publish surface | owner repo + Discord surface | release-ready or shipped proof present | eligible public update |
| Root receipt packaging | `docs/ops/**`, root validation, lock receipts | ATLAS root | cross-repo consequence or checkpoint worth preserving | stack-level proof receipt |
| Doctrine extraction | Playbook notes/contracts | Playbook owner surface | repeated stable rule/pattern/failure mode | promoted doctrine candidate |

## 1. Automated QA / LLEL Boundary

Automated QA/LLEL is the first proof boundary.

Current strong repo-owned examples:

- Fitness `npm run qa:fitness:ui-checkpoint`
- Fitness `npm run verify:mobile-regression`
- Fitness `npm run test:mobile-regression-fixtures`
- Fitness repo-owned QA/LLEL checklist and capture conventions

This boundary exists to prove:

- deterministic fixture and board parity
- repeatable UI and mobile-regression expectations
- auth-aware proof paths through a reusable QA user instead of throwaway users
- repo-owned blockers are surfaced before any release-readiness claim

Rule:

- repo blockers exposed by QA/LLEL must be fixed in the owning repo

Pattern:

- automated proof -> receipt -> targeted fix -> rerun

Failure mode:

- root-side QA logic bypasses repo failures and turns proof into approval theater

## 2. Local Desktop Server Boundary

Local desktop server proof is where the app is exercised on the real local route and environment.

Canonical intent:

- run the repo-local dev or preview server on the expected local origin
- keep local app URLs pointed at the local server
- use the owner repo env/path doctrine instead of inventing a root-side shadow runtime

This boundary proves:

- the app actually boots locally
- the route shape and manifest/static asset surfaces resolve locally
- proof is based on the real local route, not abstract fixture-only confidence

Rule:

- prefer proof from the real signed-in route first; preview or fixture routes are fallback surfaces when the real route is blocked or a narrow harness is explicitly required

Failure mode:

- operators rely on stale boards, cached paths, or root-owned assumptions instead of a live local app surface

## 3. Mobile LAN Proof Boundary

Mobile LAN proof exists because browser automation alone is not enough for all install, mobile, and device-dependent behavior.

Canonical intent:

- use the repo-owned local/mobile workflow
- keep the QA identity reusable and deterministic
- separate automated capture proof from real physical/manual device review

This boundary is where the stack distinguishes:

- local authenticated browser/mobile-loop proof
- manual device attestation
- real install and native-shell behavior that cannot be claimed from automation alone

Rule:

- physical/manual proof may satisfy device-specific review, but it must remain labeled as manual proof

Pattern:

- local browser/mobile loop -> manual device spot check where required -> release-readiness evidence

Failure mode:

- teams claim native install or physical-device confidence from browser automation alone

## 4. Browser / Manual / Plugin Proof Boundary

Browser automation and manual/plugin proof are the visual/runtime review boundary that sits between raw automation and release-readiness claims.

Current canonical sources:

- browser/plugin-assisted local proof loops
- repo-local screenshot or capture flows
- operator review of live local routes

This boundary proves:

- the intended route renders
- the expected UI family or flow is visually consistent
- manual reviewer checkpoints are attached where automation cannot fully decide

It may include:

- browser automation
- local capture scripts
- manual visual review
- narrow plugin/browser verification

It may not:

- replace underlying repo-owned automated checks
- pretend manual captures are machine-generated proof

Rule:

- fresh route-level proof beats remembered state or old screenshots

Failure mode:

- stale screenshots or fixture boards are treated as equivalent to a fresh local route capture

## 5. Release-Readiness Evidence Boundary

Release readiness is the gate that turns proof into a governed ship candidate.

This boundary should aggregate:

- automated QA/LLEL proof
- local desktop and mobile proof
- browser/manual review where required
- build and repo verification results
- known gaps and accepted exceptions

Current governed examples already visible in Fitness:

- release ledger verification sets
- QA/LLEL receipts
- `_stack` deploy-readiness doctrine

Rule:

- proof must be complete enough for the release tier being claimed

Pattern:

- repo proof -> readiness gate -> `_stack` deploy authority

Failure mode:

- teams confuse “the app looked fine once” with release-readiness evidence

## 6. Feedback Card Closeout Boundary

Feedback closeout is where shipped proof reconnects to the user/system feedback that justified the work.

Canonical Fitness pattern:

- feedback forum card
- bounded feedback row
- `feedback:board:export`
- reviewed planning input
- completion review
- optional curated public update if the shipped work is user-facing

This boundary exists to prove:

- the shipped change actually answers the reviewed card
- completion review is explicit
- raw thread mutations are not mistaken for engineering closure

Rule:

- reviewed promotion is required before Discord feedback becomes durable engineering truth

Pattern:

- feedback card -> audit comments -> board export -> reviewed task packet -> completion review

Failure mode:

- teams treat Discord thread state as if it were already release-ready engineering truth

## 7. Discord Update Proof Dependency

Discord updates depend on proof; they do not create proof.

This boundary is downstream of:

- release-readiness evidence
- deploy proof where the release/update handoff requires it
- feedback closeout when a specific shipped card should be promoted publicly

No deploy or Discord post before proof rule:

- no public `#updates` publish before governed proof exists
- no feedback-card mutation log in `#updates`
- no public update as a substitute for release evidence

Rule:

- Fitness owns identity; Discord consumes proof

Failure mode:

- public narration advances while the actual proof chain is still incomplete

## 8. ATLAS Root Receipt Packaging Boundary

ATLAS root packages the cross-repo proof consequence, not the underlying repo-owned proof itself.

ATLAS root should package:

- proof-lane inventories and convergence maps
- cross-repo checkpoints
- stack-lock decisions when repo heads move
- pause/resume receipts and validation posture

ATLAS root should not replace:

- repo-owned QA/LLEL artifacts
- repo-owned feedback board exports
- repo-owned release ledgers
- repo-owned Discord draft/publish state

Pattern:

- owner repo keeps proof artifacts; root records the coordinated interpretation

Failure mode:

- root becomes a dumping ground for duplicated proof instead of a coordination/reporting layer

## 9. Playbook Rule / Pattern / Failure-Mode Extraction

Playbook should extract stable doctrine from the proof workflow only after the evidence chain is governed and repeatable.

Strong extraction candidates from this handoff:

- repo-owned QA blocker doctrine
- reusable QA user and local auth proof pattern
- route-first proof versus stale-capture failure mode
- manual-device-proof labeling rule
- feedback-card-to-completion-review boundary
- no-deploy/no-Discord-post-before-proof rule

What Playbook should own:

- the reusable rule language
- convergence-ready pattern labels
- failure-mode classification
- promotion criteria for future workflow contracts

What Playbook should not own here:

- live local server execution
- repo-owned QA capture storage
- Discord runtime state

Rule:

- evidence is not reusable doctrine until canonicalized and promoted

## 10. No `tmp` / Source-Truth Fallback Rule

`tmp` may hold disposable captures and scratch outputs, but it must never become source truth for proof, deploy authority, or consumer state.

Allowed `tmp` usage:

- disposable screenshots
- temporary captures
- scratch inspection artifacts

Forbidden `tmp` usage:

- canonical repo replacement
- proof-source substitution when the owner repo or local route is missing
- deploy target substitution

Rule:

- disposable evidence storage is not canonical workflow authority

Failure mode:

- a broken canonical path gets silently replaced by a `tmp` surface, recreating split truth

## 11. Recommended Canonical Operator Story

The stack should present one proof story:

1. prove baseline behavior with repo-owned QA/LLEL automation
2. prove the live local route on the owner repo
3. add browser/manual/mobile proof where the route or device class requires it
4. aggregate that evidence into release readiness
5. close the feedback loop through reviewed exports and completion review
6. allow Discord updates only after proof exists
7. package cross-repo consequences in ATLAS root
8. extract stable doctrine through Playbook afterward

## Relationship To The Release / Deploy / Update Handoff

This map is the proof-side contract that feeds the already-recorded release/deploy/update handoff.

In sequence:

1. QA/LLEL and local proof produce release-readiness evidence
2. release-readiness evidence feeds `_stack` deploy authority
3. deploy proof feeds release-ledger evidence
4. release and feedback proof feed Discord update eligibility
5. ATLAS root records the cross-repo checkpoint
6. Playbook extracts reusable doctrine

That means proof is upstream of both deploy authority and public update publication.

## Remaining Gaps

- Fitness has the strongest current proof workflow, but the cross-stack contract is not yet generalized for Trove or Mazer.
- Manual device install and remote deployed-surface proof remain separate lanes and must not be mislabeled as complete here.
- Discord feedback closeout is documented, but not yet unified with a stack-wide completion-review contract.
- `_stack` proof and deploy entrypoints are stronger than the current cross-stack proof narrative; convergence is still documentation-first.

## Validation

Validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

Expected interpretation for this package:

- docs-only convergence mapping
- no deploy
- no Discord publish
- no app-code mutation
