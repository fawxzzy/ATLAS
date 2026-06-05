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

## Strict Execution Cadence

Root is a control-plane surface, not a retry loop.

Rules:

- once a blocker is known and the remaining work belongs to an owner repo, root stops opening new retry receipts for that same blocker class
- one blocked execution receipt plus one blocked proof or blocker-recheck receipt is the root stop signal for that blocker class
- before any new pass, recheck whether the exact receipt already exists durably; identical reruns are not a speed strategy
- when a lane is execution-ready, run execution -> proof or reconciliation -> ratchet as one serial cluster
- keep one root writer, one owner-repo writer, and at most one read-only scout
- marker movement requires stronger reality, not cleaner narration

Batch types:

- Batch A: owner-side unblock batch -> convert blocker, merge or preserve or archive, recheck blocker class
- Batch B: root execution cluster -> execution, proof or reconciliation, marker ratchet
- Batch C: root read-model or doctrine batch -> only when no executable owner-side work is ready

Failure mode:

- root keeps narrating a blocker that now belongs to an owner repo and pays the same blocked-retry tax again

## Current Canonical Repo / Source Truth

- Fitness owner repo: `repos/fawxzzy-fitness`
- future Discord owner repo: `repos/DiscordOS`
- ATLAS root: stack coordination and truth-map layer
- `_stack`: deploy and operator execution layer

## Current Deploy Authority

Canonical deploy authority remains:

- `_stack`

That includes the governed deploy handoff from repo-local readiness into preview or production deploy execution.
