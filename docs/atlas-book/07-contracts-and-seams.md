# Contracts And Seams

## 2026-07-12 implemented-versus-proposed override

- **Implemented v1:** `atlas.event.v1` has seven generic lifecycle contracts; it does not implement GitHub/Vercel/Supabase/Discord delivery families.
- **Implemented v1:** `atlas.codex.handoff.v1` captures structured final output and rejects transcript scraping.
- **Implemented v1:** `@atlas/contracts` v0.1.0 implements five schema families.
- **Complete Contracts v2 mesh:** all eleven fixed families have implementation foundations and independent adoption proof. The terminal KnowledgeCandidate chain preserves Atlas schema authority and exact candidate/provenance identity through Playbook's candidate-only consumer and deterministic receipt without granting doctrine-promotion authority.
- **Partial:** Playbook adoption and project command adapters do not cover the full stack.
- **Partial/stale:** Cortex advisory context/routing/synthesis exists, but live freshness, chat-style synthesis, and remote authority are incomplete.
- **Proposed:** Atlas Control ledger (including proposed SQLite), delivery event plane, persistent workspace/browser leases, historical task intelligence, and cross-project knowledge promotion.

The 2026-07-12 opening audit externalizes each gap at percentage null; no proposed seam inherits implementation status from adjacent v1 contracts.

## Purpose

This page names the cross-system contracts that let the stack split cleanly without recreating hidden coupling.

## Core Rules

- no `tmp` source-truth fallback
- no manual deploy by default
- no Discord post before proof
- no hidden shared env as a substitute for a contract
- no approval-gated mutation without explicit approval

## Deploy / Update / Proof Contracts

### Repo-local prep -> `_stack` deploy authority

Contract:

- repo-local commands prepare, verify, and build
- `_stack` is the governed deploy authority

Implication:

- release preparation is not deploy approval

### Deploy proof -> release ledger

Contract:

- shipped evidence must be recorded in owner-repo release truth before downstream publication is treated as governed

### Release proof -> Discord publication

Contract:

- Discord updates consume proof
- Discord does not create proof

Implication:

- no public updates post before governed evidence exists

### Proof / receipt handoff -> ATLAS

Contract:

- owner repo keeps runtime and proof truth
- ATLAS records cross-repo consequence and durable checkpoint summaries

## Discord / Fitness Shared Contracts

### Verification bridge

Current owner:

- Fitness

Future seam:

- Fitness issues verification proof
- DiscordOS later consumes it through an explicit contract

Rule:

- token issuance remains Fitness-owned

### `discord_member_links`

Current owner:

- Fitness

Future seam:

- explicit bridge contract

Rule:

- no blind table move before canonical owner and read/write contract are explicit

### Member-number sync

Current source of truth:

- Fitness `profiles.user_number`

Future seam:

- DiscordOS may later consume member-number context for nickname/sync behavior

Rule:

- DiscordOS does not become canonical for numbering

### Deploy-to-update handoff

Current source of truth:

- Fitness release proof and deploy truth

Future seam:

- Discord publication runtime later consumes bounded release-proof inputs

Rule:

- release proof stays upstream of Discord publication

## Supabase Ownership Seams

### Fitness-owned classes

- auth and profiles
- verification-token issuance
- core product data
- release-proof-adjacent truth

### DiscordOS-later classes

- feedback runtime state
- update draft/publish runtime state
- moderation runtime state
- message-command claims
- Music Sesh runtime state

### Contract rule

- no dual-writer assumption
- schema landing and read-only proof come before canonical writer cutover

## Vercel / Runtime Ownership Seams

### Current seam

- Fitness hosts both app/runtime and current Discord runtime

### Future seam

- Fitness keeps app/runtime and upstream proof surfaces
- DiscordOS later owns Discord runtime surfaces

### Rule

- runtime/Vercel ownership must split with env and data ownership, not before

## Remaining Approval-Gated Seams

### Fitness Supabase mutation

Approval required:

- explicit Pass 1 row subset and `create profile` scope

### Remote preview / unfurl verification

Approval required:

- explicit deploy-backed verification lane opening

### Stale Vercel surface deletion

Approval required:

- only for any remaining deletion candidate after dependency check

## No-Hidden-Coupling Rules

The stack should reject these seam failures:

- Discord runtime silently staying inside Fitness forever by convenience
- ATLAS root acting like an owner repo
- `_stack` absorbing product truth
- Playbook acting as runtime host
- Discord board state being treated as deploy or product truth
- repo-root env residue becoming the default secret lane

## First Safe Seam Moves

The first safe moves after the current docs-only checkpoint are still bounded:

1. approved DiscordOS repo bootstrap only
2. approved Fitness Supabase mutation only
3. later DiscordOS code inventory/extraction package
4. later schema landing implementation
5. later dual-read proof
6. later bounded runtime cutover

None of those are implied by this contract map alone.

## UI Standards Program Seam

Root-owned program truth:

- `docs/registry/ATLAS-UI-STANDARDS-REGISTRY.v1.json`
- `docs/standards/ATLAS-UI-STANDARDS-PROGRAM.md`
- `schemas/atlas.ui.standard-registry.v1.json`
- `schemas/atlas.ui.audit-finding.v1.json`
- `schemas/atlas.ui.remediation-card.v1.json`

Owner-repo truth:

- applicable routes, states, components, and controls
- implementation tooling and local commands
- accepted adoption profile and denominator
- produced evidence and remediation state

Atlas Book boundary:

- the Book explains and indexes accepted root contracts
- the Book is not the machine-readable standards registry
- owner adoption is not inferred from a Book entry

Playbook boundary:

- repeated, independently verified findings may become source-linked `atlas.knowledge-candidate.v2` records
- Playbook remains the doctrine owner and must review promotion
- research prose and one-off findings do not flow directly into Playbook doctrine

Projection rule:

- root candidate packets are non-live and remain `unplanned`
- no project-board, Discord, marker, release, or production state changes until an authorized owner lane executes and returns proof
