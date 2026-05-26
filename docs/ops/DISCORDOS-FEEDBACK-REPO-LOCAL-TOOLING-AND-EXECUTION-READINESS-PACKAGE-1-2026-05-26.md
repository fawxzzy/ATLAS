# DiscordOS Feedback Repo-Local Tooling And Execution-Readiness Package 1 - 2026-05-26

- Date: `2026-05-26`
- Lane: `DiscordOS feedback repo-local tooling and execution-readiness package 1`
- Mode: `docs-only tooling/readiness planning`
- Control-plane checkpoint: `main@c8214ba`

## Scope

Define the minimum repo-local tooling and execution-readiness surface DiscordOS needs before any feedback adapter execution-readiness lane can exist.

In scope:

- repo-local tooling posture for `repos/DiscordOS`
- minimum TypeScript/contract compile surface
- minimal verification command shape
- transport-neutral bridge assumption boundary for Fitness-owned executors
- next allowed execution-readiness package class

Out of scope:

- repo-local adapter implementation execution
- DiscordOS runtime activation
- DiscordOS schema/data mutation
- worker retarget
- Vercel cutover
- dual-read execution
- preview/unfurl gate reopening
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`

## Operating Posture

- ATLAS root remains the coordination and receipt layer
- this pass is tooling/readiness-planning-only
- no owner-repo tracked content is changed
- no repo-local adapter implementation is performed here
- no runtime/schema/data ownership transfer is implied
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@c8214ba6dba783176f45e08d6a3cbaf4c09cc6fd`
- `docs/ops/DISCORDOS-FEEDBACK-ADAPTER-IMPLEMENTATION-PLANNING-CHAIN-CHECKPOINT-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-LOOKUP-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-1-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPORT-STORE-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-2-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-PERMISSION-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-3-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-THREAD-SYNC-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-4-2026-05-26.md`
- `docs/ops/DISCORDOS-FEEDBACK-AUDIT-ADAPTER-IMPLEMENTATION-PLANNING-PACKAGE-5-2026-05-26.md`
- `repos/DiscordOS/README.md`
- `repos/DiscordOS/AGENTS.md`
- `repos/DiscordOS/src/contracts/feedback.ts`
- `repos/DiscordOS/src/adapters/feedback/index.ts`
- `repos/DiscordOS/src/adapters/feedback/README.md`
- `repos/DiscordOS/package.json` status: missing
- `repos/DiscordOS/tsconfig.json` status: missing

## Current Missing Tooling Surfaces

The current DiscordOS repo still has only governance-first scaffold material:

- `src/contracts/feedback.ts`
- `src/adapters/feedback/index.ts`
- `src/adapters/feedback/README.md`

The minimum repo-local tooling surface needed for later adapter execution-readiness does not exist yet:

- no root package manifest
- no TypeScript config
- no local script surface
- no adapter-focused verification command
- no packetized transport assumption for how DiscordOS code would invoke Fitness-owned executors

These are now the real blockers, not missing seam definitions.

## Minimum Readiness Target

The smallest readiness target that unlocks later execution-readiness planning is:

1. one repo-local root manifest surface
2. one narrow TypeScript config surface
3. one contract-only verification command
4. one explicit transport-neutral bridge assumption

That target is enough to discuss execution-readiness without opening execution.

## Recommended Tooling Posture

### Package Manager Posture

Minimum target:

- add one root `package.json` in `repos/DiscordOS`
- keep it npm-compatible at the script surface
- do not let package-manager choice itself become a blocker for adapter readiness

Why:

- the repo currently has no manifest at all
- the next execution-readiness lane needs a stable place for scripts and dependency declarations
- npm-compatible scripts keep the contract simple even if a later owner repo chooses a wrapper

This packet does **not** choose final dependency versions or authorize installation.

### TypeScript Config Posture

Minimum target:

- add one root `tsconfig.json`
- keep it narrow to the current contract and feedback adapter surfaces
- use no-emit validation posture first

Recommended initial inclusion scope:

- `src/contracts/**/*.ts`
- `src/adapters/feedback/**/*.ts`

Recommended initial exclusion posture:

- runtime owners
- env-bound code
- Discord worker code
- schema/data clients

Why:

- the repo needs a compile boundary before any adapter execution-readiness lane can reason about implementation shape
- no-emit compile verification is the smallest safe proof surface

## Minimum Contract-Only Compile/Test Surface

The smallest useful repo-local tooling target is:

- contract and adapter type-checking only
- zero runtime execution
- zero network or database coupling

Recommended minimum surface:

- `tsc --noEmit` over the feedback contract and adapter directories
- one tiny adapter import smoke layer to prove the bundle surface stays internally coherent

This is enough to validate:

- type exports
- interface wiring assumptions
- per-port adapter placement names

This is not enough to validate:

- real Fitness calls
- real Discord thread sync
- audit posting
- permission evaluation against live data

## Minimal Verification Command Shape

Recommended minimum verification command contract:

- `verify:feedback-adapters`

Recommended behavior:

- run narrow no-emit TypeScript verification for the feedback contract and adapter surfaces
- optionally include a tiny adapter-surface import smoke step
- remain local, deterministic, and side-effect free

The important planning outcome is not the exact script body; it is that a single repo-local verification entrypoint exists before any execution-readiness lane opens.

## Bridge / Transport Assumption Boundary

The next execution-readiness lane also needs one explicit boundary assumption for Fitness-owned executors.

Required planning rule:

- DiscordOS adapters may depend only on injected port-facing executor providers
- DiscordOS may not copy Fitness runtime logic, database code, or env-backed service code

Transport posture at this stage:

- transport-neutral
- owner-safe
- injection-first

That means this packet does **not** decide:

- direct service client
- local package import
- RPC/HTTP bridge
- worker bridge

It only decides that the first execution-readiness lane must target a provider boundary that preserves Fitness ownership and keeps DiscordOS runtime-independent.

## Checkpoint Verdict

Decision: **ready for one narrow port-level execution-readiness packet after tooling/readiness definition**

Meaning:

- the planning chain is now complete enough to name the minimal repo-local tooling target
- the next allowed lane can narrow to the first port-level execution-readiness packet
- actual adapter implementation execution is still blocked

## Allowed Next Package Classes

### Allowed Now

Allowed next package class:

- one narrow first-port adapter execution-readiness packet after tooling/readiness definition

Recommended next package:

- `DiscordOS feedback lookup adapter execution-readiness package 2`

Why this one first:

- `FeedbackLookupPort` remains the smallest and least side-effect-heavy port
- it depends on the fewest runtime assumptions
- it is the cleanest first consumer of the minimal tooling surface defined here

### Still Blocked

Still blocked:

- repo-local adapter implementation execution
- multi-port execution sequencing
- schema landing
- runtime cutover
- worker retarget
- Vercel cutover
- dual-read execution
- preview/unfurl reopening

## What The First Execution-Readiness Packet Must Decide

Before any execution lane, the next packet should answer:

- how `FeedbackLookupPort` would sit inside the minimal repo-local tooling surface
- what local stub/testing posture it would use first
- what provider contract the injected Fitness-owned lookup executor must satisfy
- what repo-local verification proof would be required before any real adapter code lands
- what rollback/no-op posture protects the repo if the first execution lane later opens

## Rule / Pattern / Failure Mode

Rule:

- Tooling/readiness planning is not implementation execution readiness.

Pattern:

- Seam planning complete -> adapter planning complete -> tooling/readiness sub-plan -> first-port execution-readiness packet -> only then reassess implementation execution.

Failure Mode:

- Tooling/readiness planning inflating into repo mutation or runtime-readiness.

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/ops/DISCORDOS-FEEDBACK-REPO-LOCAL-TOOLING-AND-EXECUTION-READINESS-PACKAGE-1-2026-05-26.md`

## Next Package

`DiscordOS feedback lookup adapter execution-readiness package 2`

Why:

- the missing shared tooling/readiness surface is now defined at the control-plane layer
- `FeedbackLookupPort` remains the safest first execution-readiness target
- runtime, schema, data, and execution still remain blocked
