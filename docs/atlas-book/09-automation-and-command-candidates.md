# Automation And Command Candidates

## Purpose

This chapter maps repeated stack work into future automation and command surfaces without skipping current approval gates or owner boundaries.

It is not an implementation plan.

It exists to answer:

- which repeated tasks are good automation candidates
- which surfaces should likely own those automations
- which work should remain human-reviewed
- which work must never be directly automated

## Repeated Operator Tasks

The stack already repeats these tasks often enough to justify command planning:

- validation after docs, receipt, and governance updates
- release prep followed by governed deploy authority
- release proof followed by Discord update drafting or publication
- feedback board sync, board exports, and card closeout review
- local QA/LLEL proof and receipt packaging
- stale surface inventory and dependency checks
- marker table updates after durable lane progress
- doctrine routing from repeated receipts and patterns
- env or secret-path classification before cleanup
- data-hygiene inventory, export, and approval packet preparation
- local normalize, redact, classify, dedupe, and minimum-payload packaging before remote export

## Candidate `_stack` Commands

`_stack` is the strongest home for commands that coordinate governed execution across repos or enforce shared release policy.

Best candidates:

- `stack validate`
  - run root validation and summarize delta against the last receipt
- `stack release prep <repo>`
  - verify repo-local release prerequisites and package proof pointers
- `stack deploy <repo>`
  - remain the canonical deploy authority wrapper
- `stack update draft <repo>`
  - open or refresh update-draft packaging only after proof exists
- `stack receipt package <lane>`
  - build a consistent receipt skeleton for cross-repo lanes
- `stack marker checkpoint`
  - render the current marker table from durable docs state
- `stack data gateway packet <lane>`
  - normalize, redact, classify, and package a minimum useful export packet with provenance metadata before remote handoff
- `stack stale-surface audit`
  - inventory duplicate deploy surfaces before deletion approval
- `stack vercel-health`
  - summarize canonical projects, churn, stale surfaces, and provenance drift for the current stack

`_stack` should not become the default home for product-specific runtime logic.

## Candidate ATLAS Root Automation Helpers

ATLAS root is the right home for automation helpers that classify cross-lane continuation safety without claiming repo-runtime ownership.

Best candidates:

- `atlas_continue_gate`
  - read one machine-readable Codex result and decide whether bounded continuation is still honest
  - admit one wrapper-bound live-shaped JSONL receipt-capture seam before any explicit execution enablement
  - admit one bounded runtime-surface proof seam when executable order or host-runtime surface materially changes
  - require explicit operator allow plus wrapper-bound JSONL capture before one bounded live command may run
  - admit only the exact real `codex exec resume --last` command shape for live execution
  - launch npm-installed Windows Codex `.cmd` shim surfaces through an explicit wrapper path instead of treating Python launcher artifacts like host-runtime truth
  - classify current-host runtime-start failures as blocked decision receipts with stable runtime-boundary labels instead of silently swapping in arbitrary proof commands
  - classify exact command-semantic failures such as `resume_requires_stdin_prompt` when live proof starts but still fails
  - probe `codex exec resume --help` to freeze prompt-argument and dash-stdin contract truth before any prompt-bearing resume variant can be admitted
  - admit one exact inline prompt argument variant before considering dash-stdin prompt injection
  - classify bounded live-proof timeout as a durable blocker such as `resume_command_timeout` instead of relying on outer shell timeout behavior
  - stop root retries after one timeout execution receipt plus one timeout-boundary recheck receipt for the same admitted branch
  - stay dry-run by default
  - stop on validator drift, widened scope, missing next move, or non-automated class attempts
  - always write durable gate-decision receipts

ATLAS root should not silently become a background job runner or unattended mutation daemon.

## Candidate Playbook Commands

Playbook is the likely home for doctrine-facing commands that extract reusable operator rules from receipts.

Best candidates:

- `playbook pattern route`
  - classify a new repeated pattern as doctrine, ATLAS-only note, automation candidate, or parked evidence
- `playbook doctrine draft`
  - create a doctrine-ready draft from receipt-backed patterns
- `playbook closeout review`
  - enforce receipt, proof, and owner-boundary checks before a lane is called durable
- `playbook workflow audit`
  - compare a workflow recipe against current practice and note drift

Playbook should remain governance-facing, not runtime-facing.

## Candidate Discord / Fawxzzy Bot Commands

Discord-side commands are best when they improve bounded workflow state without making Discord the hidden engineering source of truth.

Best candidates:

- feedback panel refresh/setup commands
- feedback card creation and bounded edit launchers
- review-state or completion-state promotion helpers
- update-draft helpers that only publish after proof exists
- Music Sesh setup or room-surface refresh commands
- operator-facing thread-pointer or board-split helpers

Good future candidates after DiscordOS separation:

- moderation queue or purgatory workflow helpers
- publication checklist helpers
- release-proof consume-and-draft helpers through explicit contracts

Discord commands should not become a backdoor for deploys, data cleanup, or silent cross-system mutations.

## What Should Remain Human-Reviewed

These surfaces still need a human in the loop even if command scaffolding exists:

- final deploy go/no-go judgment
- final public update wording and timing
- stale surface deletion confirmation
- Supabase cleanup classification and approval
- DiscordOS cutover timing
- doctrine admission
- card acceptance-criteria quality for ambiguous feature work
- brand/preview visual confirmation when manual judgment matters

## What Requires Approval Gates

The following automation classes may assist preparation, but the action itself should stay approval-gated:

- DiscordOS repo bootstrap
- Fitness Supabase mutation
- remote preview/unfurl verification lane opening
- stale Vercel surface deletion
- secret moves, rotation, or deletion
- runtime/Vercel cutover
- schema cutover or live data migration

Commands may prepare artifacts, but they should not silently cross these gates.

## What Must Never Automate Directly

These actions should not be turned into one-step unattended automation:

- deploying by bypassing `_stack`
- posting a Discord update before proof exists
- deleting live or possibly-live infrastructure on stale appearance alone
- mutating Supabase user/profile state without scoped export and rollback posture
- printing or committing secrets
- using `tmp` as a fallback source of truth
- rewriting owner boundaries by convenience

## Relationship To AI Repetition-to-Automation Pipeline

This chapter is the planning spine for that lane.

It turns repeated human work into candidate automation classes, but it also records the boundary between:

- safe preparation automation
- governed execution automation
- permanently human-reviewed decisions

Progress in this chapter should raise automation quality, not automation aggressiveness.

## Relationship To AI Long-Run Batch Orchestration

Long-run orchestration is a later layer on top of these command candidates.

The correct order is:

1. classify repeated work
2. define owner surface
3. define proof and approval boundary
4. implement bounded commands
5. only then consider long-run or chained orchestration

Without that order, batch orchestration becomes hidden policy mutation.

## First Safe Automation Candidates

These are the best first candidates because they prepare or summarize state without crossing risky mutation boundaries:

- root validation summary command
- marker checkpoint render command
- receipt skeleton generator
- guarded Codex continuation gate
- stale-surface audit inventory command
- Vercel health and churn summary command
- doctrine routing template generator
- release-proof to update-draft packaging helper
- QA/LLEL proof packet generator
- branch/worktree normalization inventory helper
- local data gateway packet scaffold with schema/version, sensitivity, provenance, and transformation-record fields

## Candidate Ownership Matrix

| Candidate class | Best owner | Why |
| --- | --- | --- |
| validation and receipt packaging | `_stack` | shared governed execution surface |
| release proof to update draft | `_stack` plus Discord contract | respects no-post-before-proof rule |
| doctrine routing and pattern extraction | Playbook | governance and reusable operator knowledge |
| Discord feedback/panel helpers | DiscordOS later, Fitness-hosted now | runtime workflow surface |
| Music Sesh setup helpers | DiscordOS later, Fitness-hosted now | runtime workflow surface |
| data-hygiene export and approval prep | owner repo plus ATLAS docs | high-risk prep needs owner context |
| local data gateway preprocessing | `_stack` first, owner repo as needed | cross-lane export discipline should become a governed shared surface before remote sync |
| Vercel health classification | Lifeline later, `_stack` first | operational health should become a first-class governed signal |

## Local Data Gateway First Implementation Surfaces

First concrete surfaces should land in this order:

1. docs contract
   - freeze the packet vocabulary before code
2. `_stack` packet helper
   - `stack data gateway packet <lane>`
3. Playbook doctrine promotion
   - reusable rule language after the contract is stable

Current admitted wrapper-stage modes:

- `validate-only`
- `emit-dry-run`
- `review-only`
- `proof-only`
- `full-local-chain`

Still never admitted:

- `send`

First workflow targets:

- Supabase review/export packet
- Vercel dependency-check packet
- DiscordOS boundary handoff packet
- future model-prompt input packet

Required packet fields for the first helper candidate:

- purpose
- schema/version
- sensitivity
- owner surface
- provenance
- transformation record
- validation status
- redaction status
- dedupe status
- downstream target class
- payload summary
- export exclusion summary
- receipt or proof reference
- minimum useful payload

Required packet lifecycle for the first helper candidate:

1. raw capture
2. local normalize
3. local validate
4. local redact/classify
5. local dedupe/extract
6. packet emit
7. downstream handoff
8. receipt/proof

Helper-specific non-goals:

- no live SaaS/API send
- no hidden export
- no secret expansion
- no direct AI/model prompt emission without packet review

Recommended first artifact root:

- `runtime/gateway-packets/<lane>/<date>/`

Selected first implementation slice:

- packet field validator

Why this slice lands first:

- it is the smallest reusable contract gate
- it proves required field enforcement before artifact emission
- it stays safely below packet generation, manifest writing, or proof packaging
- it avoids turning the first helper into a half-emitter under preview language

Current `_stack` helper entry for this slice:

- `pnpm --dir repos/_stack run data-gateway:packet:validate -- --input <packet.json>`
- `pnpm --dir repos/_stack run data-gateway:packet:emit:dry-run -- --input <packet.json> --lane <lane>`
- `pnpm --dir repos/_stack run data-gateway:packet:review -- --artifact-dir <dir> --reviewer <label> --disposition <approved|rejected|needs-revision|no-decision> [--note "<text>"]`
- `pnpm --dir repos/_stack run data-gateway:packet:proof-package -- --artifact-dir <dir>`

Current proof surface for this slice:

- `pnpm --dir repos/_stack run data-gateway:packet:validate:test`
- `pnpm --dir repos/_stack run data-gateway:packet:emit:dry-run:test`
- `pnpm --dir repos/_stack run data-gateway:packet:review:test`
- `pnpm --dir repos/_stack run data-gateway:packet:proof-package:test`

Current local artifact landing root:

- `runtime/gateway-packets/<lane>/<date>/<packet-id>/`

Current local review artifact set:

- `packet-review.md`
- `packet-review-metadata.json`

Current local proof bundle set:

- `proof-summary.md`
- `proof-metadata.json`

Wrapper recommendation after the full local proof chain:

- keep validator, emitter, review, and proof-packager as separate primitives
- add one future thin orchestrating no-send wrapper:
  - `stack data gateway packet <lane> --mode <validate-only|emit-only|review-only|proof-only|full-local>`
- require the wrapper to delegate to the existing helper family rather than reimplementing packet logic
- keep operator review explicit inside `full-local`

Review-only dispositions currently supported:

- `approved`
- `rejected`
- `needs-revision`
- `no-decision`

Deferred after this slice:

- wrapper implementation package 1
- full `stack data gateway packet <lane>` wrapper implementation
- any downstream send/transport boundary

Still explicitly prohibited after this slice:

- any send to SaaS, API, model, database, queue, or webhook target
- any `send`, `sync`, `post`, `submit`, or `mutate` helper mode
- any interpretation that local `approved` review status authorizes downstream execution

Next safe boundary after the proof-packager surface:

- real-workflow proof over packaged reviewed local artifacts
- still local-only
- still no-send

Send-capable work requires a separate authorization lane that names:

- exact target class
- exact owner surface
- exact command surface
- explicit approval class
- target type
- allowed sensitivity constraints
- exact proof, rollback, and fail-closed posture
- exact audit and receipt obligations
- explicit no-hidden-transport guarantees

The future wrapper must remain below that authorization line:

- it may orchestrate only local validate/emit/review/proof-package behavior
- it may not introduce endpoint arguments, target selectors, or any send-capable mode

Wrapper contract now frozen at the docs layer:

- `stack data gateway packet <lane> --mode <validate-only|emit-only|review-only|proof-only|full-local>`
- wrapper stays a thin no-send orchestrator over the existing helper family
- wrapper preserves:
  - explicit local input
  - explicit review disposition
  - canonical artifact root
  - receipt-ready local summary output
- wrapper must never add:
  - endpoint args
  - target selectors
  - auth inputs
  - hidden transport toggles
  - lane-specific business logic

Wrapper behavior matrix now frozen at the docs layer:

- per-mode behavior admitted:
  - `validate-only`
  - `emit-dry-run`
  - `review-only`
  - `proof-only`
  - `full-local-chain`
- each mode now has explicit:
  - required inputs
  - prerequisite artifacts
  - produced artifacts
  - receipt-ready summary outputs
  - failure exits
  - forbidden behavior
- wrapper receipt output must report:
  - invocation summary
  - artifact refs
  - validation state
  - review state
  - proof state
  - no-send attestation
  - failure summary
- wrapper still may not add:
  - send-capable modes
  - target selection semantics
  - hidden export
  - lane-specific branching logic

Current landed wrapper layer:

- wrapper implementation package 1
- package-1 modes now implemented:
  - `validate-only`
  - `emit-dry-run`
- wrapper implementation package 2
- package-2 mode now implemented:
  - `review-only`
- wrapper implementation package 3
- package-3 mode now implemented:
  - `proof-only`
- the wrapper remains a thin no-send orchestrator over the existing validator, dry-run emitter, review, and proof-packager helpers
- package 2 keeps the wrapper thin over the existing review primitive and still rejects transport-shaped and send-capable flags at the wrapper entrypoint
- package 3 keeps the wrapper thin over the existing proof-packager primitive and still rejects transport-shaped and send-capable flags at the wrapper entrypoint
- package 3 proof now confirms `proof-only` across the same three admitted workflow classes already used by the helper family
- package 4 proof now confirms `full-local-chain` across the same three admitted workflow classes already used by the helper family

Current adoptable-now workflow classes for the no-send chain:

- Supabase export / approval-prep packet workflows
- Vercel dependency / deletion decision workflows
- DiscordOS trust-boundary / provenance proof workflows

Not yet honest as blanket adoption targets:

- docs-native marker or doctrine receipts
- Discord feedback evidence families without a dedicated evidence-packet schema
- Atlas-owned repo naming execution/proof families without a rename-manifest and reconciliation schema
- Atlas-owned repo naming execution/proof families remain below admission even after the rename-manifest contract checkpoint until one proof-backed no-send family path exists without gateway-specific rename logic
- Atlas-owned repo naming families are now narrow `real-workflow proof-admitted later` candidates because the rename-manifest contract is complete, the bounded proof shape is frozen, and one bounded blocked-workflow family path is now durable
- Atlas-owned repo naming families still remain below `adoptable now` until the no-send chain proves reusable family carriage across at least one second bounded candidate without gateway-specific rename execution logic
- destructive retained-surface disposal families without a delete-manifest contract

Wrapper implementation-planning checkpoint now frozen at the docs layer:

- first actual wrapper slice is limited to:
  - `validate-only`
  - `emit-dry-run`
- package 1 should prove only thin orchestration over the existing validator and dry-run emitter helpers
- wrapper package 1 must not yet admit:
  - `review-only`
  - `proof-only`
  - `full-local-chain`
  - reviewer/disposition orchestration
  - any send-capable or target-selecting surface

Next safe wrapper layer after package 3 proof:

- wrapper package 4 planning checkpoint

Selected package-3 wrapper slice now implemented:

- `proof-only` only
- requires existing reviewed packet artifacts
- must preserve explicit no-send and no automatic full-chain behavior

Still deferred after package 3 proof:

- `full-local-chain`
- any target-selection or send-capable wrapper surface

## Non-Goals

- no command implementation
- no bot expansion in this chapter
- no new deploy path
- no approval-gate bypass
- no runtime ownership change
