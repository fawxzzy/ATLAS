# Failure Modes And Recovery

## Purpose

This chapter captures the stack failures that have repeated often enough to deserve durable prevention and recovery playbooks.

Each entry records:

- symptoms
- root cause
- prevention rule
- recovery steps
- owning lane
- required receipt
- marker impact

## 1. Wrong Repo / Wrong Branch / Wrong Deploy Path

### Symptoms

- code change lands in the wrong repo root
- a deploy comes from the wrong branch or dirty local state
- runtime behavior does not match the repo believed to own it

### Root cause

- owner boundary was assumed instead of verified
- branch or deploy authority was bypassed

### Prevention rule

- start from the owner repo
- treat `_stack` as deploy authority
- verify branch and source truth before release work

### Recovery steps

1. stop further deploys
2. identify the actual owner repo and deployment source
3. classify the incorrect deploy surface
4. restore canonical release path
5. record the correction in a receipt

### Owning lane

- Unified Workflow Convergence
- Branch & Worktree Normalization
- Manual Deploy Exception Burn-Down

### Required receipt

- deploy correction or normalization receipt

### Marker impact

- Unified Workflow Convergence
- Manual Deploy Exception Burn-Down

## 2. `tmp` Source-Truth Drift

### Symptoms

- a temporary file or scratch export starts getting treated as canonical
- docs or implementation cite `tmp` instead of the owner surface

### Root cause

- convenience overtook source-truth discipline

### Prevention rule

- no `tmp` source-truth fallback

### Recovery steps

1. identify the actual owner surface
2. move durable artifacts into the correct lane
3. update docs and receipts to point at canonical truth
4. classify any surviving `tmp` artifact as disposable only

### Owning lane

- Tmp Dependency Elimination
- Inventory & Truth Map

### Required receipt

- truth-map or cleanup receipt

### Marker impact

- Tmp Dependency Elimination
- Inventory & Truth Map

## 3. Manual Deploy Bypass

### Symptoms

- a live change exists without governed deploy proof
- platform state is correct but release evidence is missing or ambiguous

### Root cause

- deploy happened outside the `_stack` authority path

### Prevention rule

- no manual deploy by default

### Recovery steps

1. identify the deployment and provenance
2. classify whether it is canonical, stale, or scratch
3. restore governed release proof
4. record exception handling before any further deploy

### Owning lane

- Manual Deploy Exception Burn-Down

### Required receipt

- deploy exception or release handoff receipt

### Marker impact

- Manual Deploy Exception Burn-Down
- Unified Workflow Convergence

## 4. Discord Update Before Proof

### Symptoms

- a public update exists with no deploy or proof backing it
- Discord wording implies a shipped state the stack cannot prove

### Root cause

- publication boundary was crossed before proof boundary

### Prevention rule

- no Discord post before proof

### Recovery steps

1. pause further publication
2. verify whether proof exists
3. correct or retract the publication if needed
4. republish only after evidence is durable

### Owning lane

- Discord Workflow, Publication & Docs Reliability
- Unified Workflow Convergence

### Required receipt

- deploy/update/proof receipt

### Marker impact

- Discord Workflow, Publication & Docs Reliability

## 5. Supabase Profile Cleanup Without Export / Rollback

### Symptoms

- user/profile cleanup is proposed or attempted without export artifacts
- mutation scope is broad or poorly classified

### Root cause

- cleanup pressure outran governed data-hygiene workflow

### Prevention rule

- no data mutation without export, rollback posture, and explicit approval

### Recovery steps

1. stop all mutation
2. inventory affected classes
3. generate export and approval packet
4. reopen only a narrowly scoped mutation pass

### Owning lane

- Fitness Supabase Profile/Data Hygiene

### Required receipt

- inventory, decision, cleanup plan, export packet, approval packet

### Marker impact

- Fitness Supabase Profile/Data Hygiene

## 6. Secret Spill Into Repo Roots

### Symptoms

- `.env` or worker-secret files appear in repo roots
- validation or repo status shows secret-bearing residue risk

### Root cause

- secrets were staged near code for convenience

### Prevention rule

- secrets belong only in governed `secrets/**` lanes

### Recovery steps

1. confirm the governed destination
2. inventory key names only
3. move the file into the governed secret lane
4. verify source removal and git-ignore posture
5. record cleanup receipt

### Owning lane

- Operator Secret Path Hygiene

### Required receipt

- secret-path inventory, decision, cleanup-plan, and cleanup-pass receipts

### Marker impact

- Operator Secret Path Hygiene

## 7. Duplicate Vercel Project Drift

### Symptoms

- multiple projects or aliases appear to own the same runtime
- stale projects remain READY and look live from the overview

### Root cause

- scratch or one-off deploy surfaces were never fully classified or retired

### Prevention rule

- classify Vercel surfaces as canonical, stale, scratch, or cutover-target before reuse or deletion

### Recovery steps

1. inventory the duplicate surface
2. identify the canonical owner
3. run a dependency check
4. retain or delete only after explicit confirmation
5. record the result in a decommission receipt

### Owning lane

- Duplicate Surface Decommission
- Manual Deploy Exception Burn-Down
- Lifeline later for health projection

### Required receipt

- stale-surface inventory and later deletion receipt if approved

### Marker impact

- Duplicate Surface Decommission
- Manual Deploy Exception Burn-Down

## 8. Stale Branch / Worktree Replay Drift

### Symptoms

- old branches or worktrees reintroduce already-settled state
- operator loses track of which surface is active

### Root cause

- stale working surfaces were retained without clear ownership or retention class

### Prevention rule

- branch name is metadata; ownership and diff truth matter more

### Recovery steps

1. inventory branch/worktree state
2. classify active versus stale surfaces
3. preserve or archive before destructive cleanup
4. remove only after retention class is clear

### Owning lane

- Branch & Worktree Normalization

### Required receipt

- worktree or branch normalization receipt

### Marker impact

- Branch & Worktree Normalization
- Inventory & Truth Map

## 9. Brand Source / Generated / Consumer Mismatch

### Symptoms

- source asset, generated output, and consumer surface disagree
- preview looks wrong even though the asset source appears updated

### Root cause

- generated output or consuming surface was not resynced from canonical source

### Prevention rule

- canonical source -> generated outputs -> consumer sync

## 10. Raw Export / Packet Contract Drift

### Symptoms

- a remote consumer receives noisy raw input instead of a compact packet
- provenance, sensitivity, or transformation history is missing from a shared payload
- later reviewers cannot replay or audit what left local control

### Root cause

- Local Data Gateway doctrine was referenced, but no concrete packet contract was enforced

### Prevention rule

- raw data stays local-first
- exported packets must carry purpose, schema/version, sensitivity, provenance, transformation record, validation result, redaction status, dedupe status, downstream target class, and minimum useful payload

### Recovery steps

1. stop further handoff from the malformed packet flow
2. identify the local owner surface and original raw source
3. rebuild the payload through the gateway lifecycle
4. emit a contract-compliant packet
5. record the corrected packet in a receipt or proof artifact

### Owning lane

- Local Data Gateway
- AI Repetition-to-Automation Pipeline

### Required receipt

- Local Data Gateway packet contract or helper proof receipt

### Marker impact

- Local Data Gateway
- AI Repetition-to-Automation Pipeline

### Recovery steps

1. identify the canonical asset source
2. regenerate bounded outputs
3. verify consumer surfaces
4. record proof and mismatch resolution

### Owning lane

- Brand Asset Canonicalization
- Preview Cache & Surface Consistency

### Required receipt

- brand or preview verification receipt

### Marker impact

- Brand Asset Canonicalization
- Preview Cache & Surface Consistency

## 10. DiscordOS / Fitness Hidden Coupling

### Symptoms

- Discord runtime behavior depends on Fitness-owned state without an explicit contract
- ownership questions can only be answered from memory

### Root cause

- runtime and data coupling was allowed to grow inside the Fitness host surface

### Prevention rule

- shared seams must be explicit contracts, not hidden coupling

### Recovery steps

1. inventory the hidden coupling
2. classify future owner and source of truth
3. document the contract seam
4. defer migration until env, schema, and cutover plans exist

### Owning lane

- Discord OS Infrastructure Separation
- Dependency Untangling

### Required receipt

- separation inventory and shared-contract decision receipts

### Marker impact

- Discord OS Infrastructure Separation
- Dependency Untangling

## 11. Bot / Runtime Migration Without Contracts

### Symptoms

- runtime cutover is attempted before env, schema, or contract boundaries are stable
- bot continuity becomes guesswork

### Root cause

- infrastructure separation moved faster than shared-contract planning

### Prevention rule

- no runtime cutover before contract, schema, env, and rollback plans are durable

### Recovery steps

1. stop cutover work
2. restore current runtime owner if any live change started
3. finish contract, schema, and cutover planning
4. reopen only as a staged migration

### Owning lane

- Discord OS Infrastructure Separation

### Required receipt

- shared-contract, env/runtime, schema, and cutover plan receipts

### Marker impact

- Discord OS Infrastructure Separation
- Discord Workflow, Publication & Docs Reliability

## 12. Cache-Only Preview Confusion Versus Source Drift

### Symptoms

- a preview looks stale, but source truth may actually be correct
- teams cannot quickly tell cache error from real source mismatch

### Root cause

- cache invalidation and source-truth verification were not separated clearly

### Prevention rule

- verify source truth first, then classify cache or delivery drift

### Recovery steps

1. confirm canonical source state
2. verify generated artifacts if applicable
3. inspect the preview or delivery layer separately
4. record whether the issue was source drift or cache-only drift

### Owning lane

- Preview Cache & Surface Consistency
- Inventory & Truth Map

### Required receipt

- preview verification receipt

### Marker impact

- Preview Cache & Surface Consistency
- Inventory & Truth Map

## 13. Raw Data Export Before Local Refinement

### Symptoms

- raw logs, tables, exports, or screenshots are sent directly to an AI, API, SaaS tool, remote database, or teammate
- exported payloads have no clear purpose, provenance, or sensitivity boundary
- the same noisy cleanup work repeats by hand in each lane

### Root cause

- local preprocessing was treated as optional instead of the default boundary

### Prevention rule

- raw data lands locally first
- remote systems receive minimum useful packets, not messy raw dumps

### Recovery steps

1. stop further export or mutation
2. identify the raw local source
3. normalize, validate, redact, classify, dedupe, and extract useful signal locally
4. rebuild the payload with purpose, schema or version, sensitivity label, provenance, and transformation record
5. record the gateway receipt before resuming remote work

### Owning lane

- Local Data Gateway
- Operator Secret Path Hygiene
- Fitness Supabase Profile/Data Hygiene when the data domain is profile or auth state

### Required receipt

- local data gateway or export packet receipt

### Marker impact

- Local Data Gateway
- Operator Secret Path Hygiene
- Fitness Supabase Profile/Data Hygiene when applicable

## 14. Fake Motion After Green

### Symptoms

- repo/runtime truth is already green, but workers keep opening new repair, install-readiness, or reconciliation packets anyway
- a lane that is blocked only by a live external bridge keeps attracting more ATLAS/root or owner-repo churn
- restart surfaces become noisy enough that future sessions cannot tell the remaining blocker is outside repo truth

### Root cause

- the blocker boundary was not frozen explicitly once owner-scope setup was already ruled out
- operators kept treating an external/session bridge defect like a local repo/runtime defect

### Prevention rule

- `Session-Scoped External Blocker Freeze`: when repo/runtime truth is green and the only missing proof depends on a live external/session bridge, freeze all repo/root mutation until one live bridge success occurs
- `Upstream Product Fault Hold`: when owner-scope setup has already been ruled out and the remaining blocker is a product/runtime defect outside repo truth, freeze the lane and preserve only restart-relevant truth

### Recovery steps

1. stop opening new owner-repo repair, install-readiness, or cleanup packets
2. classify the remaining blocker explicitly as not a default-browser issue, not an ATLAS/root issue, and not a Fitness repo/runtime issue
3. point restart surfaces to the canonical bug packet instead of recreating narrative churn
4. reopen only after one successful live Codex-to-Chrome runtime call exists from a responsive session
5. route immediately to `Fitness Discord Default-profile post-install governed authenticated same-event fresh-submit positive live proof capture pass 9`

### Owning lane

- Discord OS Feedback Workflow Canonicalization
- Truth Map & ATLAS Book
- Knowledge Capture & Transfer
- Durable Context Externalization

### Required receipt

- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-POST-INSTALL-CODEX-CHROME-BRIDGE-TIMEOUT-BOUNDARY-RECEIPT-2026-06-01.md`
- `docs/ops/ROOT-BOUNDED-DISPATCHER-RECONCILIATION-AFTER-FITNESS-DISCORD-POST-INSTALL-CODEX-CHROME-BRIDGE-TIMEOUT-BOUNDARY-RECEIPT-CLOSEOUT-2026-06-01.md`

### Marker impact

- Discord OS Feedback Workflow Canonicalization
- Truth Map & ATLAS Book
- Knowledge Capture & Transfer
- Durable Context Externalization

## 15. Manual Toggle Drift

### Symptoms

- a proof loop works only when the operator remembers hidden flags, prompts, browser state, or setup order
- local runtime, proof capture, and receipt packaging all exist, but the end-to-end loop still cannot be replayed reliably
- readiness claims sound stronger than the actual repeatability of the loop

### Root cause

- the proof parts were treated as equivalent to a deterministic proof loop
- fresh capture still depends on one-off operator stitching instead of a governed local spine

### Prevention rule

- `Proof-Loop Before Pixel-Loop`: do not claim UI iteration readiness until the proof-capture path is deterministic enough to verify Codex-applied changes without ad hoc operator stitching
- `Local-First Verification Spine`: when local runtime, proof capture, and truth update all exist, readiness still requires binding them into one deterministic loop

### Recovery steps

1. inventory the loop end to end: request/spec intake, mutation, local runtime, proof capture, receipt update
2. separate already-proven segments from the still-manual links
3. classify any blocker as owner-local, ATLAS/control-plane, or external/session-scoped
4. freeze one exact readiness threshold before claiming promotion
5. promote only after one bounded loop reruns end to end without hidden toggles

### Owning lane

- Feedback Loop Readiness
- Fitness QA/LLEL Workflow
- AI Repetition-to-Automation Pipeline

### Required receipt

- `docs/ops/FEEDBACK-LOOP-READINESS-DETERMINISTIC-READINESS-THRESHOLD-PASS-1-2026-06-01.md`

### Marker impact

- Feedback Loop Readiness
- Fitness QA/LLEL Workflow
- AI Repetition-to-Automation Pipeline

## 16. Automation Claim Inflation

### Symptoms

- repeated operator work gets described as automation-ready even though the trigger or proof path is still unstable
- a helper-friendly preparation step gets conflated with the full workflow it supports
- externally blocked proof capture gets misclassified as local automation debt

### Root cause

- repetition was counted, but the trigger, inputs, proof artifact, failure boundary, and fallback path were not all frozen together
- operator frustration was treated like automation evidence

### Prevention rule

- `Automation Follows Stable Repetition`: do not promote a repeated workflow into automation candidacy until its trigger, inputs, proof artifact, and fallback path are all explicit and stable
- `Operator Repetition Ledger`: capture repeated operator actions as named families with trigger, boundary, proof expectation, and safe fallback so helper work targets real repetition instead of vague friction
- `Bounded Automation Candidate Ladder`: manual repetition -> structured repetition -> automation candidate -> automation-ready

### Recovery steps

1. name the repeated family explicitly
2. separate safe preparation helpers from full execution claims
3. record the trigger surface, stable inputs, proof artifact, failure boundary, and safe fallback
4. classify any dependency on hidden toggles, ad hoc prompting, or external/session defects as a non-automation boundary
5. promote only after one real governed operator surface exists with repeatable proof

### Owning lane

- AI Repetition-to-Automation Pipeline
- Playbook Everywhere + Cortex Interface
- `_stack` Readiness

### Required receipt

- `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-AUTOMATION-CANDIDATE-THRESHOLD-PASS-1-2026-06-01.md`
- `docs/ops/FEEDBACK-LOOP-READINESS-DETERMINISTIC-READINESS-THRESHOLD-PASS-1-2026-06-01.md`

### Marker impact

- AI Repetition-to-Automation Pipeline
- Playbook Everywhere + Cortex Interface
- `_stack` Readiness

## 17. Agent Premature Entanglement

### Symptoms

- Cortex agents start appearing as if they own workflow truth instead of consuming an explicit contract
- prompt roles or repeated frustration are treated like agent readiness
- a shadow scaffold implies authority over proof, deploy, publication, or owner-truth actions
- ATLAS and Cortex both start defining readiness truth for the same family independently

### Root cause

- the agent family was introduced before the repetition contract, fallback, and owner boundary were frozen
- Cortex was allowed to infer capability from prompts instead of loading explicit governed contracts
- the export surface did not stay truth-owned by ATLAS/Playbook before Cortex consumption widened

### Prevention rule

- `Cortex Follows Governed Repetition`: Cortex agents may only be introduced from already-governed repetition families with explicit trigger, input, proof, fallback, and owner-boundary truth
- `Contract-First Agent Shadowing`: define the contract first and let the agent shadow the workflow before any authority is granted
- `Contract Before Agent`: no Cortex agent surface should exist without a governed contract exported from ATLAS/Playbook truth
- `Truth-Owned Interface Export`: ATLAS defines the contract; Cortex consumes it without owning readiness truth

### Recovery steps

1. route the family back to the repetition ledger and freeze the missing contract fields
2. strip any implied production authority from the agent surface
3. separate bounded preparation helpers from human-judgment or externally blocked classes
4. reload Cortex only from the exported contract surface
5. collapse any duplicate readiness truth back into the ATLAS/Playbook export surface
6. promote only after bounded consumption proof exists without drift

### Owning lane

- Playbook Everywhere + Cortex Interface
- Cortex Readiness
- AI Repetition-to-Automation Pipeline

### Required receipt

- `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-FIRST-AGENT-SHADOWING-PASS-1-2026-06-01.md`
- `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-EXPORT-SURFACE-PASS-3-2026-06-02.md`
- `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-AUTOMATION-CANDIDATE-THRESHOLD-PASS-1-2026-06-01.md`

### Marker impact

- Playbook Everywhere + Cortex Interface
- Cortex Readiness
- AI Repetition-to-Automation Pipeline

## 18. Route Past Dirty Root

### Symptoms

- validation is green, but the shared ATLAS root checkout is still broadly dirty
- workers keep opening new root lanes or publication claims from the same dirty checkout anyway
- future sessions cannot tell whether a changed root file is old residue, current execution, or unclassified retained state

### Root cause

- green validation was treated like permission to ignore shared checkout hygiene
- dirty-root state was narrated indirectly through downstream lanes instead of being frozen as its own blocker

### Prevention rule

- `Shared Root Cleanliness Gate`: when the ATLAS root is a shared active writer surface and `git status` shows broad modified or untracked root-owned state, freeze new lane claims and publication decisions until that dirty state is explicitly classified or intentionally preserved
- `Classify Before Cleanup`: read-model blocker -> dirty-root inventory -> ownership and retention split -> explicit preserve/cleanup decision -> only then resume lane advancement

### Recovery steps

1. stop opening new root execution or publication lanes from the same dirty checkout
2. capture the dirty-root scope directly from `git status --porcelain=v1 --untracked-files=all`
3. distinguish the blocker from any already-closed validator or stack-lock family
4. record whether each surface is active work, retained evidence, or unclassified residue before any cleanup is proposed
5. resume deferred lanes only after the root worktree is explicitly stabilized or intentionally preserved

### Owning lane

- Truth Map & ATLAS Book
- Cortex Readiness
- Branch & Worktree Normalization

### Required receipt

- `docs/ops/STABILIZE-ROOT-WORKTREE-BLOCKER-CLASSIFICATION-AND-HOLD-PASS-1-2026-06-01.md`
- `docs/ops/CORTEX-READINESS-READ-MODEL-FRESHNESS-AND-DEFERRED-LANE-PASS-4-2026-06-01.md`

### Marker impact

- Truth Map & ATLAS Book
- Cortex Readiness
- Branch & Worktree Normalization

## Recovery Pattern

Across these failure modes, the common recovery order is:

1. stop further mutation or publication
2. re-establish source truth
3. classify owner boundary
4. preserve or export before delete
5. restore proof
6. record the receipt
