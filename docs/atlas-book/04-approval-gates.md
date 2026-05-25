# Approval Gates

## Current Approval-Gated Lanes

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

## Closed Gates Recently Resolved

### DiscordOS repo bootstrap

Status:

- completed on 2026-05-25

Result:

- `repos/DiscordOS` now exists as the canonical local repo surface
- governance scaffold only
- no code migration
- no env files
- no runtime mutation

### Vercel stale Spotify-surface deletion

Status:

- completed on 2026-05-25

Result:

- `spotify-club-phase-7-interaction-reliability` deleted
- `spotify-board-hygiene-main` deleted
- canonical Fitness project unchanged

## No-Mutation Defaults

Without explicit approval:

- no Fitness Supabase mutation
- no DiscordOS runtime cutover by implication from the completed bootstrap
- no DiscordOS schema or Vercel mutation by implication from planning docs
- no bot restart or retarget
- no remaining stale-Vercel cleanup by appearance alone

## Why These Gates Exist

These gates prevent:

- hidden cross-lane shortcuts
- runtime drift
- irreversible data cleanup without rollback posture
- silent service mutation from planning work
