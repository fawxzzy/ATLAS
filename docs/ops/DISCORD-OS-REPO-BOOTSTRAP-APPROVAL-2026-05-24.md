# Discord OS Repo Bootstrap Approval

Date: 2026-05-24
Lane: Discord OS Infrastructure Separation
Mode: docs-only approval packet
Status: bootstrap implementation approval packet prepared

## Goal

Prepare the exact approval-gated first implementation step for creating the canonical local DiscordOS repo surface, without moving code or touching any live runtime, data, or deployment surface.

This pass does not:

- create `repos/DiscordOS`
- clone the remote
- initialize Git locally
- move code
- mutate Supabase
- mutate Vercel
- restart the bot
- post to Discord
- pull env
- print secrets

## Inputs

- `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-INVENTORY-2026-05-24.md`
- `docs/ops/DISCORD-OS-SHARED-CONTRACT-DECISION-PASS-1-2026-05-24.md`
- `docs/ops/DISCORD-OS-ENV-RUNTIME-OWNERSHIP-MATRIX-2026-05-24.md`
- `docs/ops/DISCORD-OS-SUPABASE-SCHEMA-LANDING-PLAN-2026-05-24.md`
- `docs/ops/DISCORD-OS-RUNTIME-VERCEL-CUTOVER-PLAN-2026-05-24.md`
- `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-PLAN-2026-05-24.md`

## Exact Target

### Local path

- `repos/DiscordOS`

### Remote

- `https://github.com/fawxzzy/DiscordOS.git`

### Branch expectation

- `main`

## Bootstrap Scope

If approved later, Bootstrap Pass 1 is limited to:

- clone the existing remote into `repos/DiscordOS`
- verify remote identity and branch posture
- optionally add a minimal governance scaffold only if separately approved

### Allowed scaffold only if explicitly approved

- `README.md`
- repo-local `AGENTS.md`
- minimal `docs/ops/` placeholder structure
- minimal verify-command placeholder contract if needed

### Explicit non-goals for Bootstrap Pass 1

- no Fitness code migration
- no Discord runtime migration
- no bot worker retarget
- no env files
- no secret files
- no Supabase schema work
- no Supabase row movement
- no Vercel project creation or linking
- no Discord posting
- no stack-wide runtime registration changes by implication

## Exact Future Implementation Boundary

If the owner later approves bootstrap-only implementation, the implementation should stop after one of these two bounded outcomes:

### Outcome A: empty canonical clone

- `repos/DiscordOS` exists
- Git remote is correct
- branch is `main`
- working tree is clean
- no scaffold changes added

### Outcome B: clone plus minimal governance scaffold

- all Outcome A conditions
- plus explicitly approved bootstrap scaffold only
- still no application code movement
- still no env, Supabase, Vercel, or runtime change

## Verification Requirements

Any future Bootstrap Pass 1 implementation must verify:

### Git remote identity

- `origin` equals `https://github.com/fawxzzy/DiscordOS.git`

### Branch

- checked-out default branch is `main`

### Working tree

- repo status is clean after clone or approved scaffold commit

### Path ownership

- `repos/DiscordOS` is the only local canonical repo path used
- no temporary extraction repo or alternate path becomes source truth

### ATLAS registration decision

If bootstrap creates a real local repo surface, the implementation pass must explicitly decide whether any ATLAS stack registration note needs to be added.

Rule:

- do not silently change `stack.lock.yaml`
- do not silently alter stack registration assumptions
- if registration changes are needed, treat that as a separate bounded decision

### Root validation

- run `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

## Rollback / No-Op Posture

### No-op default

Without explicit approval:

- no repo is created
- no clone happens
- no scaffold is added
- Fitness remains the only live Discord runtime owner

### If clone fails

- no further action is taken
- no partial scaffold should be invented elsewhere
- no other repo path should be used as fallback

### If scaffold is not approved

- the repo remains an empty clean clone
- no code movement follows
- no runtime or data dependency may point to DiscordOS yet

### If bootstrap later needs to be abandoned

- local repo can remain unused until a later explicit cleanup decision
- no live state should depend on its existence

## Live Dependency Rule

After bootstrap, and before any later migration lane:

- no bot runtime should point at DiscordOS
- no webhook should point at DiscordOS
- no Supabase write path should point at DiscordOS
- no Vercel project should be linked by implication
- no secret lane should be populated by env pull

Bootstrap does not activate anything.

## Approval Checklist

The owner must explicitly approve all applicable items before implementation:

- approve clone into `repos/DiscordOS`
- approve remote `https://github.com/fawxzzy/DiscordOS.git`
- approve `main` as canonical branch
- approve whether bootstrap is:
  - empty clone only
  - clone plus minimal governance scaffold
- confirm no Fitness code migration yet
- confirm no Discord runtime change yet
- confirm no Supabase migration yet
- confirm no Vercel mutation yet

## Required Approval Language

Implementation should only proceed after explicit owner language equivalent to:

`Approve DiscordOS repo bootstrap only into repos/DiscordOS, no code migration.`

If the owner wants scaffold too, approval should be equivalently explicit, such as:

`Approve DiscordOS repo bootstrap plus minimal governance scaffold only, no code migration.`

## First Safe Post-Bootstrap Package

After a successful approved bootstrap, the next clean move should still be bounded and low-risk:

- repo-local governance scaffold refinement, if not already landed
or
- a docs-only extraction inventory package inside `repos/DiscordOS`

It should not be:

- full Discord route extraction
- worker retargeting
- Supabase schema implementation
- Vercel project creation
- Music Sesh migration

## Command / Tool Boundary For Future Bootstrap Pass

The future implementation pass should be limited to:

- Git clone/init and remote verification
- minimal local file creation only if separately approved
- local validation

It should not use:

- Supabase mutation tools
- Vercel mutation tools
- Discord posting flows
- env pull flows

## Marker Interpretation

This packet justifies:

- Discord OS Infrastructure Separation: `65%`

It does not justify:

- repo creation by itself
- code movement
- Supabase mutation
- Vercel mutation
- bot restart
- runtime cutover
