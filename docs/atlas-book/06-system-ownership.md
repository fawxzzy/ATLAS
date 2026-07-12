# System Ownership

## 2026-07-12 capability ownership override

| Capability | Current owner / boundary |
|---|---|
| root governance, marker truth, v1 contracts, accepted receipts | ATLAS root |
| canonical workspace writer, operator commands, event normalization | `_stack` |
| doctrine and repo verification | Playbook |
| advisory context/routing/synthesis | root-owned Cortex; remote Cortex is not adopted |
| product and code truth | each owner repository |
| board/publication/readback mutation | DiscordOS as one logical writer; Fitness direct overlap is debt |
| remote source, CI, review, releases, security signals | GitHub |
| delivery and observability | Vercel |
| auth and persistence | Supabase |
| bounded execution tasks | Codex |
| project routing | ATLAS MAIN; existing Mazer; Fitness after security gates; DiscordOS embedded |
| backend-neutral durable coordination ledger | **PROPOSED** Atlas Control |

READY deployments, clean worktrees, historical 100% markers, chat handoffs, and continuity projections are never owner implementation or current-health proof.

## Purpose

This page names the current and future owner surfaces across the stack so work can reopen inside the correct lane without reconstructing boundaries from chat history.

## ATLAS Root Ownership

ATLAS root owns:

- stack topology and path policy
- markers and lane state
- cross-repo receipts and checkpoint packaging
- truth-map and ATLAS Book structure
- validation posture and stack-level reporting
- cross-repo convergence maps

ATLAS root does not own:

- product runtime behavior
- repo-local release ledgers
- Discord runtime state
- deploy execution authority

## `_stack` Ownership

`_stack` owns:

- governed preview and production deploy authority
- deploy preflights and fail-closed identity checks
- shared operator execution surfaces
- shared Codex runner/orchestration
- operator-facing execution wrappers

`_stack` does not own:

- product truth
- Discord board truth
- Playbook doctrine truth
- owner-repo runtime semantics

## Foundation Ownership

Foundation owns:

- its own product/runtime truth
- its own repo-local implementation and verification surfaces

At this checkpoint, Foundation remains primarily a named systems lane in ATLAS planning rather than an active cross-lane mutation surface here.

## Lifeline Ownership

Lifeline owns:

- its own repo-local product and runtime truth
- its own implementation and verification surfaces

ATLAS root may record Lifeline-facing checkpoints, but does not replace Lifeline as owner.

## Playbook Ownership

Playbook owns:

- reusable governance doctrine
- rules, patterns, and failure-mode promotion
- verify/plan/apply semantics
- contract language and reusable workflow framing

Playbook does not own:

- live deploy execution
- repo-local product proof
- Discord runtime behavior

## Cortex Ownership

Cortex may own:

- planning context consumption
- prioritization and admission-facing read models later

Cortex does not currently own:

- runtime behavior
- doctrine promotion
- repo mutation authority

## Fitness Ownership

Fitness owns:

- app/runtime behavior
- product and UX work
- local/mobile proof and QA/LLEL
- Fitness auth and profiles
- canonical `user_number` truth
- release preparation and release ledger truth
- verification-token issuance
- current live Discord runtime hosting
- current live Discord operational tables until separation lands

Fitness should not permanently own:

- future DiscordOS platform/runtime code by default

## DiscordOS Future Ownership

DiscordOS is the future owner for:

- Discord interaction/runtime
- feedback workflow/runtime state
- updates draft and publication runtime
- moderation runtime
- Music Sesh runtime
- Discord bot process ownership
- DiscordOS Supabase for Discord-owned tables
- Discord-first env and runtime ownership

Current status:

- bootstrapped
- local repo now exists at `repos/DiscordOS`
- governance scaffold only
- no code moved
- no runtime cutover

## Supabase Project Ownership

### Fitness Supabase

Project:

- `lpswxoyfniocuhljgzbc`

Owns:

- Fitness auth and profile truth
- Fitness product tables
- verification-token issuance truth
- current live Discord/Music Sesh operational tables until separation

### DiscordOS Supabase

Current state:

- Supabase project `DiscordOS` exists at ref `nwexsktuuenfdegzrbut`
- private schema `discordos` exists
- feedback runtime contract tables are landed with RLS enabled and no public policies
- Fitness remains live runtime truth until an explicit cutover packet proves parity

Project:

- `nwexsktuuenfdegzrbut`

Future owner for:

- Discord-owned runtime/workflow state after migration

Current status:

- healthy
- empty
- no schema landing implemented yet

## Vercel Project Ownership

### Current

Fitness Vercel currently owns:

- live Discord interaction runtime
- current Discord update/runtime surfaces
- Music Sesh runtime
- Fitness app routes and product runtime

### Future split

Fitness Vercel should keep:

- Fitness app/runtime
- verification issuance surfaces
- release-proof upstream surfaces

DiscordOS Vercel should later own:

- Discord interaction/runtime
- Discord publication/runtime
- Music Sesh runtime

## Ownership Summary

### Current owner map

- ATLAS root: coordination and truth-map
- `_stack`: deploy/operator execution
- Playbook: doctrine
- Fitness: product truth plus current Discord hosting

### Future owner map

- Fitness: product truth
- DiscordOS: Discord runtime truth
- ATLAS root: stack coordination truth
- `_stack`: shared execution truth
- Playbook: promoted governance truth
