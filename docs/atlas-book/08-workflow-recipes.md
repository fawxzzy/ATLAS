# Workflow Recipes

## Purpose

This chapter turns the current operating model into reusable “run this workflow” recipes so future work can start from the correct owner surface instead of relying on chat reconstruction.

## Recipe 1: Product Change Workflow

### Owner

- owner repo

### Starting point

- the product’s canonical repo root

### Allowed commands / surfaces

- repo-local verify/build/test commands
- repo-local docs and proof surfaces
- `_stack` only when the work reaches governed deploy authority

### Proof required

- repo-local verification
- any app-specific proof required by the owner repo

### Receipt required

- repo-owned proof or release receipt if the change matters beyond a local edit
- ATLAS receipt only if there is cross-repo or stack consequence

### Approval gates

- deploy authority still requires `_stack`
- mutation in approval-gated data lanes remains separate

### Forbidden shortcuts

- do not start product implementation from ATLAS root
- do not treat release-prep as deploy approval

### Marker impact

- usually moves product-specific lanes, not ATLAS systems lanes first

## Recipe 2: QA / LLEL Proof Workflow

### Owner

- owner repo

### Starting point

- repo-local QA/LLEL and local route proof surfaces

### Allowed commands / surfaces

- repo-local QA/LLEL commands
- local desktop route proof
- local mobile/LAN proof
- browser/manual review where required

### Proof required

- deterministic QA baseline
- live local route confirmation
- manual/device proof clearly labeled when used

### Receipt required

- repo-owned proof receipt
- ATLAS proof receipt only when a cross-repo checkpoint matters

### Approval gates

- remote preview/unfurl verification remains separately approval-gated

### Forbidden shortcuts

- no stale screenshot proof
- no `tmp` source-truth fallback
- no labeling manual device checks as automated proof

### Marker impact

- Fitness QA/LLEL Workflow
- Unified Workflow Convergence
- Knowledge Capture & Transfer when generalized

## Recipe 3: Release / Deploy / Update Workflow

### Owner

- owner repo, then `_stack`, then Discord publication surface

### Starting point

- repo-local release prep

### Allowed commands / surfaces

- repo-local release prep and verify commands
- `_stack` deploy wrappers and preflights
- repo-owned release ledger
- Discord update draft/publish surface after proof

### Proof required

- repo-local readiness
- `_stack` deploy success
- release-ledger evidence

### Receipt required

- owner-repo release evidence
- ATLAS receipt if stack consequence or lane state changed

### Approval gates

- no manual deploy by default
- no Discord post before proof

### Forbidden shortcuts

- no direct deploy by implication from a build
- no public update before evidence exists

### Marker impact

- Unified Workflow Convergence
- Manual Deploy Exception Burn-Down
- Discord Workflow, Publication & Docs Reliability

## Recipe 4: Discord Feedback Card Workflow

### Owner

- current Fitness-hosted Discord runtime
- future Discord work lane after separation

### Starting point

- Discord feedback forum and bounded row

### Allowed commands / surfaces

- approved feedback panel/actions
- forum thread updates and bounded row sync
- reviewed board export

### Proof required

- bounded card content
- reviewed promotion before implementation truth
- completion review before final shipped closure

### Receipt required

- thread audit history in Discord
- reviewed export artifacts where needed
- ATLAS receipt only if workflow doctrine or stack consequence changes

### Approval gates

- shipped closure and completion-review posture still apply

### Forbidden shortcuts

- do not treat the forum thread as engineering truth by itself
- do not auto-post card changes to `#updates`

### Marker impact

- Discord Workflow, Publication & Docs Reliability
- Feedback Loop Readiness
- Knowledge Capture & Transfer when promoted

## Recipe 5: Brand / Preview Verification Workflow

### Owner

- ATLAS planning plus owner repo proof

### Starting point

- brand or preview verification receipt and owner repo surfaces

### Allowed commands / surfaces

- repo-local proof and asset verification
- ATLAS receipts and verification maps
- `_stack` only when a deploy-backed proof lane is explicitly opened

### Proof required

- source truth and consumer path proof
- live preview proof only when the explicit lane is opened

### Receipt required

- ATLAS or repo-local verification receipt depending on owner boundary

### Approval gates

- remote preview/unfurl verification is approval-gated

### Forbidden shortcuts

- no remote preview assumptions from local-only evidence
- no stale surface treated as canonical

### Marker impact

- Brand Asset Canonicalization
- Preview Cache & Surface Consistency
- Inventory & Truth Map

## Recipe 6: Supabase Data Hygiene Workflow

### Owner

- owner repo plus governed data-hygiene lane

### Starting point

- inventory, decision pass, cleanup plan, export packet, approval packet

### Allowed commands / surfaces

- read-only inventory and classification
- export and rollback planning
- mutation only after explicit approval

### Proof required

- exact row/class scope
- export artifacts
- rollback posture
- validation after any future mutation

### Receipt required

- inventory receipt
- decision receipt
- cleanup plan
- export packet
- approval packet
- later mutation receipt if approved

### Approval gates

- Fitness Supabase mutation remains explicitly approval-gated

### Forbidden shortcuts

- no bulk cleanup by implication
- no touching deferred Discord/Music Sesh tables casually

### Marker impact

- Fitness Supabase Profile/Data Hygiene
- Operator Secret Path Hygiene

## Recipe 7: DiscordOS Separation Workflow

### Owner

- Discord work lane, with ATLAS systems coordination

### Starting point

- inventory, shared contracts, env/runtime ownership, schema landing plan, cutover plan, and completed bootstrap receipt

### Allowed commands / surfaces

- docs-only planning
- completed bounded repo bootstrap
- later bounded schema and runtime lanes

### Proof required

- explicit contract seams
- env/runtime ownership split
- schema landing plan
- runtime/Vercel cutover plan
- bootstrap receipt

### Receipt required

- each planning receipt in the separation chain
- bootstrap receipt
- later schema and cutover receipts

### Approval gates

- bootstrap is complete
- code migration or runtime mutation still requires a bounded implementation package and receipt

### Forbidden shortcuts

- no code movement by implication from bootstrap
- no hidden Fitness coupling preserved as the default
- no Vercel or Supabase mutation from planning docs

### Marker impact

- Discord OS Infrastructure Separation
- Dependency Untangling
- Post-Convergence Lane Split Readiness

## Recipe 8: Branch / Worktree Normalization Workflow

### Owner

- ATLAS systems lane and owner repo where needed

### Starting point

- worktree/branch inventory and normalization receipts

### Allowed commands / surfaces

- inventory
- classification
- bounded cleanup after confirmed retention and owner rules

### Proof required

- path truth
- ownership truth
- retention class

### Receipt required

- normalization inventory or disposal receipt

### Approval gates

- active repo move/rename or destructive cleanup still requires explicit caution

### Forbidden shortcuts

- no deleting active repo or worktree state without confirmed retention posture

### Marker impact

- Branch & Worktree Normalization
- Canonical Repo Restoration
- Inventory & Truth Map

## Recipe 9: Duplicate Surface Decommission Workflow

### Owner

- ATLAS systems lane with owner-surface confirmation

### Starting point

- inventory and decision receipts for duplicate surfaces

### Allowed commands / surfaces

- inventory
- dependency check
- later bounded deletion or alias cleanup after explicit approval

### Proof required

- current canonical surface identified
- stale surface dependency check complete
- deletion risk classified

### Receipt required

- inventory receipt
- decision pass
- later disposal receipt if approved

### Approval gates

- any remaining stale Vercel surface deletion still requires explicit approval

### Forbidden shortcuts

- no deleting stale-looking surfaces without final dependency verification

### Marker impact

- Duplicate Surface Decommission
- Manual Deploy Exception Burn-Down

## Recipe 10: Pattern / Doctrine Extraction Workflow

### Owner

- Playbook with ATLAS root projection

### Starting point

- receipt-backed repeated rule, pattern, or failure mode

### Allowed commands / surfaces

- convergence maps
- doctrine routing
- Playbook-facing promotion
- ATLAS documentation of the cross-repo consequence

### Proof required

- receipt-backed evidence
- clear owner boundary
- reusable wording

### Receipt required

- matrix, routing, or doctrine-promotion receipt

### Approval gates

- doctrine promotion still depends on stable evidence, not chat-only insight

### Forbidden shortcuts

- no promoting one-off chat comments into doctrine
- no using Playbook as runtime owner

### Marker impact

- Core Pattern Convergence
- Playbook Everywhere + Cortex Interface
- Knowledge Capture & Transfer
- AI Repetition-to-Automation Pipeline
