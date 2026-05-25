# Post-Convergence Lane Split Readiness

Date: 2026-05-24
Lane: Post-Convergence Lane Split Readiness
Mode: docs-only planning
Status: first lane-split readiness plan recorded

## Goal

Define how work should split after convergence into three major lanes so Fitness app work, Discord work, and ATLAS systems work can progress without recreating hidden coupling or cross-lane shortcut habits.

This pass does not:

- mutate repos
- mutate Supabase
- mutate Vercel
- post to Discord
- restart bots or runtimes
- move code
- reopen approval-gated lanes by implication

## Inputs

- `docs/ops/UNIFIED-WORKFLOW-CONVERGENCE-INVENTORY-2026-05-24.md`
- `docs/ops/UNIFIED-RELEASE-DEPLOY-UPDATE-HANDOFF-2026-05-24.md`
- `docs/ops/UNIFIED-QA-LLEL-LOCAL-PROOF-HANDOFF-2026-05-24.md`
- `docs/ops/UNIFIED-DISCORD-OS-WORKFLOW-BOUNDARY-2026-05-24.md`
- `docs/ops/UNIFIED-OPERATOR-ENTRYPOINT-COMMAND-LADDER-2026-05-24.md`
- `docs/ops/UNIFIED-PLAYBOOK-CORE-PATTERN-HANDOFF-2026-05-24.md`
- `docs/ops/DISCORD-OS-REPO-BOOTSTRAP-APPROVAL-2026-05-24.md`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-MUTATION-PASS-1-APPROVAL-2026-05-24.md`

## Governing Rules

- Owner lanes must reopen by scope, not by convenience.
- Discord consumes proof; it does not create deploy, product, or ATLAS truth.
- `_stack` remains deploy and shared operator authority where already governed.
- Playbook remains the reusable governance and doctrine owner.
- Approval-gated lanes stay paused until explicit owner approval is given.
- No cross-lane shortcut should recreate the current bundled Fitness-hosted Discord OS posture by accident.

## Three-Lane Model

After convergence, the stack should default to three major operating lanes:

1. Fitness app lane
2. Discord work lane
3. ATLAS systems lane

These lanes may coordinate through explicit contracts, but should not silently share ownership.

## 1. Fitness App Lane Scope

The Fitness app lane owns Fitness product truth and app-facing execution.

### Included scope

- product and UX work
- app routes and runtime behavior
- local desktop proof
- mobile and LAN proof
- QA/LLEL
- release preparation and release ledger maintenance
- Fitness-auth and profile ownership
- Fitness Supabase profile and data hygiene when explicitly approved
- Fitness verification-token issuance
- Fitness account settings and Discord Connector UX

### Excluded by default

- DiscordOS runtime platform code
- Discord feedback runtime ownership
- Discord publication runtime ownership
- Music Sesh platform ownership once DiscordOS migration opens
- ATLAS governance automation implementation

### Rule

- Fitness app lane should not own Discord platform/runtime code by default once lane splitting becomes active

## 2. Discord Work Lane Scope

The Discord work lane owns Discord-first workflow and runtime surfaces.

### Included scope

- DiscordOS
- bot/runtime behavior
- Discord interaction handling
- feedback workflow and board lifecycle
- updates draft and publication workflow
- moderation and purgatory workflow
- Music Sesh / Spotify Club runtime
- DiscordOS Supabase
- Discord workflow, publication, and docs reliability
- Discord-facing panels, command cards, and bounded operator controls

### Excluded by default

- Fitness auth/profile canonical ownership
- Fitness release-proof source truth
- direct ATLAS governance ownership
- hidden access to Fitness-owned tables without a contract

### Rule

- the Discord lane must not preserve hidden Fitness coupling as a long-term operating model

## 3. ATLAS Systems Lane Scope

The ATLAS systems lane owns stack governance, coordination, validation, and shared execution surfaces.

### Included scope

- ATLAS root
- `_stack`
- Foundation
- Lifeline
- Playbook
- Cortex
- stack validation
- markers, inventories, maps, and checkpoint docs
- root receipts and lock posture
- governance automation and operator-ladder hardening

### Excluded by default

- product-owned app UX work
- Discord community runtime feature work
- repo-local product data mutation unless explicitly routed

### Rule

- ATLAS systems lane coordinates and governs; it does not casually absorb owner-repo runtime truth

## Shared Contracts Between Lanes

The future split only works if shared seams stay explicit.

### Deploy / update handoff

- Fitness release proof remains upstream
- Discord publication remains downstream
- ATLAS records stack-visible consequence

### Proof / receipt handoff

- repo-owned proof stays in the owner repo
- ATLAS records cross-repo interpretation and lane consequence
- Playbook extracts reusable doctrine from the evidence

### Feedback closeout

- Discord board state remains operational signal
- reviewed closeout and completion review remain bounded workflow gates
- shipped card closure should not become repo or ATLAS truth without review and proof

### Playbook doctrine extraction

- stable rules, patterns, and failure modes promote into Playbook after receipt-backed evidence
- lanes consume doctrine but do not each reinvent it

### Discord publication boundary

- no Discord post before proof
- no `#updates` publication without governed upstream evidence

### Supabase contract seams

- Fitness profile/auth truth stays Fitness-owned
- DiscordOS runtime state moves later to DiscordOS-owned storage
- shared seams such as verification bridge, member links, member-number sync, and deploy-to-update handoff stay explicit

## Entry Criteria For Reopening Each Lane

### Fitness app lane

May reopen for active execution when:

- scope is product, proof, QA/LLEL, release readiness, or explicitly approved Fitness Supabase hygiene work
- no hidden DiscordOS platform migration is smuggled in
- any approval-gated Fitness Supabase mutation has explicit owner approval

### Discord work lane

May reopen for active execution when:

- scope is DiscordOS runtime, workflow, board, update, moderation, or Music Sesh work
- approval packet exists for any gated bootstrap or migration step
- Fitness-owned seams are consumed only through explicit contracts

### ATLAS systems lane

May reopen for active execution when:

- scope is governance, validation, `_stack`, Playbook, Cortex, markers, root receipts, or automation planning
- owner-repo mutation is not being done from root by convenience

## Forbidden Cross-Lane Shortcuts

The following shortcuts should be treated as regressions:

- doing DiscordOS platform work inside Fitness by default once the Discord lane is active
- using Discord board state as if it were deploy proof or repo truth
- using ATLAS root docs to mutate owner-repo runtime behavior by implication
- using `_stack` as a product repo
- using Playbook as a runtime host
- treating release-prep commands as deploy authority
- treating product work as if it belongs in Discord because feedback originated there
- treating Discord runtime migration as if it can bypass Fitness contract seams
- reopening approval-gated mutation lanes without explicit approval

## Required End-Of-Chat Marker Table

After the lane split becomes the normal posture, end-of-chat state should always make these visible:

- which lane was active
- whether any lane stayed paused
- whether approval-gated work was intentionally not started
- resulting marker movement

Minimum marker families to keep visible when relevant:

- Unified Workflow Convergence
- Dependency Untangling
- Discord OS Infrastructure Separation
- Fitness Supabase Profile/Data Hygiene
- Post-Convergence Lane Split Readiness

## Approval-Gated Lanes

The following lanes remain explicitly paused unless separately approved:

### DiscordOS repo bootstrap

Required phrase remains:

`Approve DiscordOS repo bootstrap only into repos/DiscordOS, no code migration.`

### Fitness Supabase mutation

No write should occur until the owner explicitly approves the exact row subset and mutation scope described in the approval packet.

### Remote preview / unfurl verification

This remains a separate deploy-backed lane and should not be reopened casually from local or docs-only work.

## First Recommended Package In Each Future Lane

### Fitness app lane

Recommended first package:

- the first explicit approved Fitness Supabase mutation pass
or
- a bounded product/QA/LLEL package that stays purely Fitness-owned

### Discord work lane

Recommended first package:

- approved DiscordOS repo bootstrap only

After that:

- a docs-only extraction inventory inside `repos/DiscordOS`
before any runtime code movement

### ATLAS systems lane

Recommended first package:

- operator-ladder or lane-readiness automation planning
or
- doctrine promotion pass for the now-stable convergence maps

## Recommended Operating Order After Split

1. keep approval-gated mutation and migration lanes paused by default
2. reopen the lane whose owner boundary is already explicit
3. force cross-lane work through written contracts
4. package cross-repo consequence in ATLAS root
5. extract reusable doctrine only after the lane work produces stable evidence

## No-Mutation Confirmation

This plan does not authorize:

- DiscordOS bootstrap implementation
- Fitness Supabase mutation
- DiscordOS schema implementation
- DiscordOS Vercel creation
- bot worker retargeting
- remote preview/unfurl verification

## Marker Interpretation

This package justifies:

- Post-Convergence Lane Split Readiness: `15%`
- Unified Workflow Convergence: `65%`
- Dependency Untangling: `30%`

It does not yet justify:

- lane split implementation
- DiscordOS bootstrap implementation
- Fitness Supabase mutation
- remote preview or deploy-backed verification reopening
