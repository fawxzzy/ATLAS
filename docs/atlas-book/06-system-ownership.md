# System Ownership

## 2026-07-15 capability ownership override

| Capability | Current owner / boundary |
|---|---|
| root governance, marker truth, v1 contracts, accepted receipts | ATLAS root |
| governed workspace/action routing, operator commands, event normalization | `_stack`; not the Discord writer |
| doctrine and repo verification | Playbook |
| private local operator cockpit | Playbook Observer on loopback, when owner-activated |
| local supervision and logon restore | Lifeline, when owner-activated |
| advisory context/routing/synthesis | event-triggered root-owned Cortex artifacts; remote Cortex is not adopted |
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

- the hosted read-only portfolio surface
- its own repo-local implementation and verification truth
- public presentation without operator action authority

Foundation production returned HTTP 200 on 2026-07-15. It is not the private
operator cockpit and must not duplicate Playbook Observer.

## Lifeline Ownership

Lifeline owns:

- local supervision, bounded restart, logs, and current-user logon restoration
- its own repo-local implementation and verification truth

The implementation exists, but the local runtime is currently unavailable:
dependencies, `dist/cli.js`, retained runtime state, and startup registration are
absent. ATLAS root may record Lifeline-facing checkpoints, but does not replace
Lifeline as owner. Activation must place mutable state and logs under
`runtime/lifeline/playbook-observer`, not inside an owner repository.

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

Playbook Observer is the intended private local operator cockpit on
`127.0.0.1:4300`. It is implemented but currently unavailable: no listener is
present and the current generated CLI entrypoint cannot start because the local
dependency install is incomplete.

## Cortex Ownership

Cortex owns event-triggered advisory read-model artifacts under
`runtime/cortex/**`. Its principal `latest` current-state, context, and operator
surfaces are currently stale at 2026-07-06. Cortex does not own doctrine
promotion, scheduling, daemon behavior, or repo mutation authority.

## Fitness Ownership

Fitness owns:

- app/runtime behavior
- product and UX work
- local/mobile proof and QA/LLEL
- Fitness auth and profiles
- canonical `user_number` truth
- release preparation and release ledger truth
- verification-token issuance
- explicit Fitness-retained product and interaction seams

Fitness does not own:

- the current DiscordOS public writer, durable Discord state, or scheduled poller

## DiscordOS Ownership

DiscordOS is the current owner for:

- Discord interaction/runtime
- feedback workflow/runtime state
- updates draft and publication runtime
- moderation runtime
- Music Sesh runtime
- Discord bot process ownership
- DiscordOS Supabase for Discord-owned tables
- Discord-first env and runtime ownership

Current status:

- hosted Vercel API and logical writer are operational
- DiscordOS Supabase state, service-role writer, persisted writer, and transfer state report ready
- GitHub Actions scheduled polling is active and the latest 2026-07-15 run succeeded
- interaction-first reliability remains a separate five-scenario proof lane

## Supabase Project Ownership

### Fitness Supabase

Project:

- `lpswxoyfniocuhljgzbc`

Owns:

- Fitness auth and profile truth
- Fitness product tables
- verification-token issuance truth
- Fitness-retained product data

### DiscordOS Supabase

Project:

- `nwexsktuuenfdegzrbut`

Owns:

- Discord-owned durable runtime and workflow state
- persisted writer and live transfer state

Current status:

- operational through current DiscordOS runtime-health readback
- service-role, writer, and transfer components ready with no blocked reasons

## Vercel Project Ownership

### Current split

Fitness Vercel owns:

- Fitness app/runtime
- verification issuance surfaces
- release-proof upstream surfaces

DiscordOS Vercel owns:

- Discord interaction/runtime
- Discord publication/runtime
- Music Sesh runtime
- runtime-health, writer, and transfer APIs

Foundation Vercel owns the hosted read-only portfolio and does not share
operator-cockpit authority.

## Ownership Summary

### Current owner map

- ATLAS root: coordination and truth-map
- `_stack`: deploy/operator execution
- Playbook: doctrine
- Fitness: product truth
- DiscordOS: Discord runtime truth
- Foundation: hosted read-only portfolio
- Playbook Observer: private local operations cockpit when activated
- Lifeline: local supervision and logon restore when activated
- Cortex: event-triggered advisory read models
- ATLAS root: stack coordination truth
- `_stack`: shared execution truth
- Playbook: promoted governance truth
