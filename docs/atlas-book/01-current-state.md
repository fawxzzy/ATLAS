# Current State

## Snapshot

The stack is currently at a clean post-closeout-pass checkpoint.

What is true right now:

- Fitness remains the live app and the live Discord-hosted runtime owner.
- DiscordOS separation is planned, scaffolded, and bounded, and the canonical local repo surface now exists.
- the DiscordOS lookup-local boundary chain is fully ratcheted shut; no further repo-local lookup widening is open without higher-level authorization.
- Fitness Supabase profile/data hygiene is closed as a governed lane at `100%`.
- Discord and Music Sesh profile/data concerns are no longer Fitness hygiene debt and now belong to DiscordOS Infrastructure Separation.
- `_stack` remains the governed deploy authority for approved app lanes.
- ATLAS root remains the coordination, receipt, and marker layer.
- Playbook remains the reusable governance and doctrine owner.
- normal stack validation is green in the current working state.
- `--allow-missing-locked-repos` is no longer needed for current validation.

## Canonical Source Truth By Surface

### Fitness

- product runtime and UX
- QA/LLEL and local/mobile proof
- Fitness auth and profiles
- Fitness release proof
- current live Discord runtime hosting

### DiscordOS

- future Discord-first runtime owner
- future feedback/update/moderation/Music Sesh runtime owner
- future DiscordOS Supabase owner for Discord-owned tables

Current status:

- local repo now exists at `repos/DiscordOS`
- contract docs, typed seams, adapter stubs, and lookup boundary receipts exist
- no code moved
- no runtime cutover

### `_stack`

- governed deploy authority
- shared operator execution
- deploy wrappers and preflights

### ATLAS root

- markers and lane state
- cross-repo receipts
- truth-map and convergence mapping
- stack validation and coordination posture

### Playbook

- reusable governance doctrine
- rules, patterns, and failure-mode promotion
- contract semantics

## Current Paused Or Gated Work

- remote preview/unfurl verification is approval-gated
- DiscordOS schema, runtime, and data migration remain unstarted and must stay receipt-bounded
- the Fitness Discord pass-9 proof lane is frozen under `Session-Scoped External Blocker Freeze`:
  - not a default-browser issue
  - not an ATLAS/root issue
  - not a Fitness repo/runtime issue
  - remaining fault domain is the Codex desktop <-> Chrome extension handshake/runtime in the current session
  - reopen only after one successful live Codex-to-Chrome runtime call exists from a responsive session
  - immediate next move once reopened: `Fitness Discord Default-profile post-install governed authenticated same-event fresh-submit positive live proof capture pass 9`
- `Feedback Loop Readiness` now has one deterministic threshold packet:
  - request/spec intake, mutation governance, local runtime truth, and receipt/truth update are already real
  - deterministic proof capture remains the missing replayable link
  - no marker movement is earned until one bounded loop reruns end to end without hidden operator stitching
- `AI Repetition-to-Automation Pipeline` now has one automation-candidate threshold packet:
  - first-safe candidate families are bounded preparation helpers such as validation summaries, marker checkpoints, receipt packaging, doctrine routing, release-proof packaging, and QA/LLEL proof-packet preparation when proof is already admissible
  - fresh live proof capture across the frozen bridge path, final go or no-go judgment, final publication judgment, doctrine admission, and destructive cleanup approval remain explicitly non-automation families
  - no marker movement is earned until one candidate family graduates into a real governed operator surface with repeatable proof and safe fallback
- `Playbook Everywhere + Cortex Interface` now has one contract-first shadowing packet and one governed contract-export packet:
  - ATLAS and Playbook remain the canonical truth surfaces for repetition families, proof expectations, fallbacks, owner boundaries, and non-claim boundaries
  - every exportable Cortex-facing family contract now freezes `contract_id`, `family_name`, `trigger`, `stable_inputs`, `expected_proof_artifact`, `fallback_path`, `owner_boundary`, `non_claim_boundary`, and `admissibility_state`
  - exportable-now families are `validation-summary-shadow`, `marker-checkpoint-shadow`, and `receipt-doctrine-draft-shadow`
  - no additional family is frozen as `shadow-only` in this packet; later candidates stay outside the export surface until their exact proof artifact and fallback boundaries are frozen
  - blocked families remain fresh live proof capture through the frozen bridge path, final deploy or publication judgment, doctrine admission, destructive cleanup or secret approval, and ambiguous visual or acceptance review
  - Cortex may only consume exported contracts and shadow bounded preparation families such as validation summaries, marker checkpoints, and receipt or doctrine draft helpers
  - `validation-summary-shadow` is now consumed safely into a local Cortex artifact with authority explicitly false, which clears the first interface threshold without widening production authority
  - lane reselection is now clean: `stabilize-root-worktree` remains a held blocker family, but the active root truth packet is `Playbook Everywhere + Cortex Interface` Wave 1A rather than another root-worktree packet
  - no marker movement is earned from the contract-export packet because it froze reusable truth without widening proof-backed consumption or owner authority
- `Cortex Readiness` now has a second bounded shadow-consumption proof:
  - `marker-checkpoint-shadow` now consumes the ATLAS marker and restart surfaces into a local Cortex artifact with ratchet authority explicitly false
  - Cortex runtime breadth now includes two distinct authority-free consumer proofs without widening governance, receipt, or owner-truth ownership
- `Cortex Readiness` now has a third bounded shadow-consumption proof:
  - `receipt-doctrine-draft-shadow` now consumes governed doctrine and failure-mode sources into a local draft-only Cortex artifact with doctrine-admission and receipt-finalization authority explicitly false
  - the current safe shadow family set is now fully consumed on the live Cortex surface without widening governance, receipt, or owner-truth ownership
- `Cortex Readiness` now has one bounded read-model projection proof:
  - `operator_surface` now projects the three current safe shadow-consumption artifacts into one existing Cortex status surface with authority still explicitly false
  - broader `current-state`, `rail-state`, and `context` freshness remains a separate next step rather than implied by this projection
- `Cortex Readiness` now has one bounded read-model freshness proof:
  - `current-state`, `rail-state`, and `context` now all acknowledge the operator-surface shadow projection as explicit evidence
  - the immediate blocker lane is now explicit as `stabilize-root-worktree`, while the deferred Cortex lane remains `promote-cortex-receipt-interpretation-consumption-feedback-wave11`
  - reported validation posture remains `critical=0 error=0 warning=494 info=0`, but no new validation was run in the contract-export pass and the shared root checkout itself remains broad dirty state, so no worktree-cleanliness claim is reopened here
  - the dirty-root posture is now durably split into active current-tranche restart surfaces, root registry/policy mirrors, mixed tracked governance support, durable-but-uncommitted `docs/ops/*` and continuity-manifest backlog, active Cortex support surfaces, and retained `archive/*` evidence, so later stabilization can classify preserve/disposition honestly instead of treating the whole checkout as one cleanup blob
  - the dominant untracked buckets now have preserve/retain posture frozen explicitly: `docs/ops/*` stays durable control-plane backlog, `docs/memory/initiatives/*` stays durable continuity backlog, and `archive/*` stays retained evidence with no delete or move decision earned
  - the tracked dirty-root surfaces now also have explicit hold classes: active current-tranche tracked work, coupled root truth mirrors/policy surfaces, and mixed tracked governance/memory/QA support backlog, so the blocker is fully classified and the remaining question is stabilization routing rather than more inventory churn
  - the stabilization route is now also frozen explicitly: preserve the active current-tranche tracked work plus coupled root truth mirrors/policy surfaces as one intentional held root tranche, keep the mixed tracked governance/memory/QA support backlog as a later independent hold, and do not claim commit/staging readiness yet
  - the first future stageable boundary is now also frozen explicitly: the minimum subset candidate is the root-worktree receipt chain plus `docs/PLAYBOOK_NOTES.md`, `docs/atlas-book/01-current-state.md`, `docs/atlas-book/05-receipt-index.md`, and `docs/atlas-book/12-restart-and-handoff-guide.md`; truth mirrors, older Cortex/read-model files, and mixed support backlog remain outside that subset by default
  - truth-mirror carry is now also frozen explicitly: none of the seven coupled root truth mirrors or policy surfaces need to join that first future stageable subset, so they remain a later adjacent hold rather than part of the blocker-preservation minimum
  - residual active-tranche carry is now also frozen explicitly: none of the earlier Cortex/read-model book or test surfaces join that first future stageable subset, so they also remain a later adjacent hold unless a new direct dependency is evidenced
  - staging-honesty posture is now also frozen explicitly: that subset may be described only as a preserved future-stageable candidate, not as presently stage-ready or commit-ready
  - blocker-facing reopen is now also frozen explicitly: the materially closed root-docs stabilization ladder stays closed, but the broader `stabilize-root-worktree` lane reopens at the dirty-worktree handling boundary because the refreshed Cortex read spine still surfaces the live blocker cleanly
  - the active dirty-worktree blocker is now classified as a `selective-staging candidate`, not as stage-ready or commit-ready and not as a reason to reopen the closed wording ladder
  - the exact next move is now one explicit selective-staging task over the minimum blocker-preservation subset: the root-worktree receipt chain through pass 10 plus `docs/PLAYBOOK_NOTES.md`, `docs/atlas-book/01-current-state.md`, `docs/atlas-book/05-receipt-index.md`, and `docs/atlas-book/12-restart-and-handoff-guide.md`
  - truth mirrors, residual Cortex/read-model surfaces, mixed tracked governance support, durable-but-uncommitted `docs/ops/*` backlog outside the receipt chain, continuity-manifest backlog, and retained `archive/*` evidence all remain held outside that task by default
  - selective-staging proof is now also frozen explicitly: the admitted minimum blocker-preservation subset has now been staged in isolation once without pulling truth mirrors, residual Cortex/read-model surfaces, mixed support backlog, continuity manifests, or retained `archive/*` evidence into the index
  - the broader dirty-root blocker still remains active outside that staged subset, so this is a bounded index-isolation proof rather than a broader clean-root or commit-ready claim
  - staged-subset disposition is now also frozen explicitly: the isolated staged subset remains held as the minimum blocker-preservation tranche, while commit-intent stays unopened and broader dirty-root state remains outside the tranche
  - commit-intent is now also frozen explicitly: the exact staged blocker-preservation tranche may now be treated as an honest partial-commit question, but only for that exact subset and not as a broader root commitability claim
  - first partial-commit conversion is now also frozen explicitly: commit `1b25ba3` preserved the minimum blocker-preservation tranche without touching the broader dirty-root state
  - post-first-commit reselection is now also frozen explicitly: the next exact tracked candidate is the residual active tranche of six atlas-book restart surfaces, four Cortex read-model files, and four Cortex read-model tests
  - residual active-tranche staging is now also frozen explicitly: that fourteen-file tranche is admitted and staged in isolation without pulling truth mirrors, mixed tracked support backlog, or broader untracked backlog into the index
  - residual active-tranche commit path is now also frozen explicitly: the staged tranche remains held, targeted read-model tests pass, validator posture still holds, and commit-intent is admissible for that exact tranche only
  - second partial-commit conversion is now also frozen explicitly: commit `c2b20be7` preserved the residual active tranche without touching the truth-mirror set, mixed tracked support backlog, or broader untracked backlog
  - truth-mirror staging and commit path is now also frozen explicitly: the remaining seven-file mirror set is admitted, staged in isolation, and may now carry commit-intent as an exact next partial-commit question
  - the mixed tracked support backlog is now also frozen explicitly as three later buckets rather than one blob: a canonicalization-support tranche, a continuity-support tranche, and a residual QA/Cortex support carry
  - the first mixed tracked support subtranche is now also frozen explicitly: canonical repo-path support refreshes across root docs, support tooling, repo-inventory validation, and delayed rename-aligned support surfaces may be preserved without pulling continuity-manifest refreshes, workflow cleanup residue, or held Cortex support into the same packet
- no helper-Vercel project deletion gate remains open after the 2026-05-25 helper-surface deletion pass
- DiscordOS lookup widening is closed at the owner-repo boundary:
  - transport-aware opening: `no`
  - externally-executing opening: `no`
  - any further DiscordOS lookup widening now requires explicit higher-level authorization
- the Playbook external `.codex/worktrees/*` stranded-directory subset and the behind-only smoke branch class are now consumed:
  - no external Playbook stranded-directory residue remains in that filesystem-only class
  - no behind-only Playbook smoke branch residue remains
  - no Playbook-only retained-surface execution subset is currently open
  - the Lifeline merged-checkpoint trio is now consumed
  - the remaining pressure is Playbook stash/manual-review governed retains plus Lifeline safety/evidence/manual-review surfaces only
  - that remaining retained-surface pressure is now governed-retain truth rather than an exact open cleanup subset

## Current Closeout Read

What the latest closeout passes proved:

- branch/worktree pressure is classified and no longer blocked by the Lifeline missing-config class
- `tmp` is no longer acting as production-critical source truth
- the remaining helper Vercel project class is closed; duplicate-surface pressure is no longer centered on live helper projects
- unrelated Fitness residue is classified enough to keep it out of DiscordOS, Supabase, and stack closeout lanes
- Fitness profile-core cleanup is fully closed; no unresolved unknown-profile, never-signed-in auth-only, or legacy automation-mismatch class remains in that lane
- the remaining automation mismatch class is governed no-op and the remaining sign-in-bearing auth-only class is governed heuristic exclusion
- Discord and Music Sesh data concerns are now explicitly transferred to DiscordOS Infrastructure Separation instead of lingering as Fitness cleanup residue
- the DiscordOS lookup-local planning and boundary chain is complete enough to stop widening without an explicit new authorization
- root self-lock sequencing for `stack.lock.yaml#stack` has been resolved by policy, so the remaining pressure is retained-surface cleanup rather than root commitability
- the retained-surface lane is no longer blocked by broad ambiguity, the Lifeline merged-checkpoint trio `lifeline-main-closeout`, `lifeline-main-closeout-2`, and `lifeline-main-closeout-3` is now consumed, and the remaining pressure is governed-retain rather than an unconsumed exact cleanup subset
- the convergence-wave closeout itself is now complete; the remaining pressure belongs to separate governed-retain or approval-gated lanes rather than residual closeout debt

## Current Direction

The stack is moving from convergence and cleanup toward explicit lane separation:

1. Fitness app lane
2. Discord work lane
3. ATLAS systems lane

## Current Vercel Pressure

The live Vercel surface is materially cleaner than the earlier convergence checkpoint, but not fully closed.

What is true right now:

- `fawxzzy-fitness` remains the highest-churn operational project and is still carrying both product runtime and Discord-hosted runtime responsibilities.
- the two stale Spotify-era Vercel projects were deleted on 2026-05-25 after dependency clearance.
- the two helper Fitness Vercel projects were also deleted on 2026-05-25 after a clean dependency check:
  - `fitness-deploy-green-panels`
  - `fitness-prod-rollout-20260525`
- deployment provenance is still mixed between governed Git-backed deploys and more ad hoc `HEAD` or dirty-state style deploy metadata.
- the recent 30-day Vercel overview is still polluted by the older Discord polling behavior, so short-window views matter more when checking whether the event-driven fix actually helped.

Why this matters:

- Lifeline should later classify every Vercel surface as canonical, helper, stale, scratch, or cutover-target.
- deploy provenance and stale-surface pressure should become visible health signals, not remembered context.
- DiscordOS separation and later Vercel health classification become easier once Lifeline can show service ownership and deploy health clearly.
