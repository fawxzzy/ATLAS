# Approval Gates

## Current Approval-Gated Lanes

### DiscordOS repo bootstrap

Status:

- paused until explicit approval

Required phrase:

`Approve DiscordOS repo bootstrap only into repos/DiscordOS, no code migration.`

Current limit:

- no local repo creation
- no code movement
- no Supabase mutation
- no Vercel mutation
- no bot/runtime change

### Fitness Supabase mutation

Status:

- paused until explicit approval of exact row subset and `create profile` scope

Current limit:

- no Supabase writes
- no auth deletion
- no profile mutation
- no Discord or Music Sesh table touch

### Remote preview / unfurl verification

Status:

- paused until an explicit deploy-backed verification lane is opened

Current limit:

- no remote mutation or verification by implication from local proof work

### Vercel stale surface deletion

Status:

- paused pending final dependency check and explicit deletion approval

Current limit:

- no project deletion
- no alias removal
- no DNS mutation

## No-Mutation Defaults

Without explicit approval:

- no DiscordOS bootstrap implementation
- no Fitness Supabase mutation
- no DiscordOS schema implementation
- no DiscordOS Vercel creation
- no bot restart or retarget
- no stale Vercel surface deletion

## Why These Gates Exist

These gates prevent:

- hidden cross-lane shortcuts
- runtime drift
- irreversible data cleanup without rollback posture
- silent service mutation from planning work
