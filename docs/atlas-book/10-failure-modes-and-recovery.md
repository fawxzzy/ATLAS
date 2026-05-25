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

## Recovery Pattern

Across these failure modes, the common recovery order is:

1. stop further mutation or publication
2. re-establish source truth
3. classify owner boundary
4. preserve or export before delete
5. restore proof
6. record the receipt
