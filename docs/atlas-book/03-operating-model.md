# Operating Model

## Canonical Owner Split

### Fitness app lane

Owns:

- app/runtime behavior
- product UX
- QA/LLEL
- local and mobile proof
- release preparation
- Fitness auth/profile truth
- approved Fitness Supabase hygiene work

Does not own by default:

- future DiscordOS platform/runtime code

### Discord work lane

Owns:

- DiscordOS runtime
- feedback/update/moderation workflows
- Music Sesh runtime
- Discord publication reliability
- DiscordOS Supabase runtime state

Does not own by default:

- Fitness auth/profile truth
- Fitness release-proof truth

### ATLAS systems lane

Owns:

- ATLAS root
- `_stack`
- Foundation
- Lifeline
- Playbook
- Cortex planning surfaces
- stack validation
- markers, receipts, and governance automation planning

## Cross-Lane Workflow Spine

Canonical flow:

1. owner repo or owner lane generates proof
2. `_stack` executes governed deploy actions where required
3. release or proof receipts are recorded in the owner surface
4. Discord consumes proof only after that proof exists
5. ATLAS root records cross-repo consequence
6. Playbook extracts reusable doctrine afterward

## Current Canonical Rules

- no manual deploy by default
- no Discord post before proof
- no `tmp` source-truth fallback
- Discord board state is operational signal, not engineering truth by itself
- approval-gated lanes do not reopen by implication

## Current Canonical Repo / Source Truth

- Fitness owner repo: `repos/fawxzzy-fitness`
- future Discord owner repo: `repos/DiscordOS`
- ATLAS root: stack coordination and truth-map layer
- `_stack`: deploy and operator execution layer

## Current Deploy Authority

Canonical deploy authority remains:

- `_stack`

That includes the governed deploy handoff from repo-local readiness into preview or production deploy execution.
