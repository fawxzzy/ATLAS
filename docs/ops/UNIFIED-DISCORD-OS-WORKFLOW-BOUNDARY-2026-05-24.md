# Unified Discord OS Workflow Boundary

Date: 2026-05-24
Lane: Unified Workflow Convergence
Mode: docs-only boundary map
Status: Discord workflow baseline recorded

## Goal

Unify the Discord-facing workflow boundaries around feedback intake, updates publishing, completion review, release-ledger dependency, bot and operator commands, and public versus private surface separation.

This pass does not post to Discord, change bot behavior, deploy, mutate Vercel, mutate Supabase, or change app code.

## Governing Rules

- Discord is the community surface, not the ATLAS control plane.
- Discord board state is operational signal, not engineering truth by itself.
- Feedback-card mutations do not auto-post to `#updates`, ATLAS, or GitHub.
- No Discord update post may publish before proof exists.
- Release posts announce shipped user-facing changes; thread audit comments document card history.
- Fitness owns identity; Discord consumes proof.
- Direct Discord-to-repo and Discord-to-ATLAS writes are not approved workflow defaults.

## Canonical Discord OS Chain

1. Feedback forum/card lifecycle
2. Private testing/canary boundary
3. Completion review boundary
4. Release-ledger and shipped-proof dependency
5. `#updates` publish boundary
6. Bot commands versus panel boundary
7. Public/product versus operator/admin boundary
8. Discord OS ownership boundary
9. ATLAS durable-truth boundary
10. Playbook doctrine extraction boundary

## Boundary Map

| Stage | Canonical entrypoint | Owner | Required proof before handoff | Output |
| --- | --- | --- | --- | --- |
| Feedback lifecycle | Discord Feedback forum + bounded DB row | Fitness Discord OS surface | structured card plus bounded row | visible community board item |
| Private canary | `feedback-testing` and other private review surfaces | Fitness Discord OS surface | bounded test intent | non-public workflow proof |
| Completion review | reviewed export + completion-review queue | Fitness planning/review surface | shipped work or resolved review candidate | completion decision |
| Release-ledger dependency | repo-owned release ledger and shipped proof | Fitness repo + release flow | shipped evidence and verification set | durable release evidence |
| `#updates` publish | Update Bot draft/publish flow | Fitness Discord OS surface | release proof and curated copy | public update post |
| Bot/panel commands | slash commands, modal panels, operator scripts | Fitness Discord OS surface | bounded command context | controlled mutation or review action |
| Public vs admin | public channels, private admin flows, operator scripts | Discord OS + operators | right audience and right proof tier | channel-safe outcome |
| Durable truth | ATLAS receipts, repo docs, exports, ledgers | ATLAS root + owner repo + Playbook | reviewed promotion | durable internal truth |

## 1. Feedback Forum / Card Lifecycle

The feedback forum is the visible community board.

Canonical model:

- Discord Feedback Forum = user-visible board
- Supabase `discord_feedback_reports` = bounded source index
- board exports = planning bridge
- reviewed prompts/tasks = implementation start

Canonical lifecycle:

1. user submits or updates feedback through approved Discord surfaces
2. Fitness stores the bounded row
3. Discord thread and starter post remain the visible board surface
4. status changes and sync actions create compact thread audit comments
5. operator exports reviewed board artifacts
6. reviewed items become planning input

Rule:

- the Discord board is the visible community board, not a second engineering task system

Pattern:

- feedback card -> status tags -> board export -> reviewed Codex task or Playbook triage artifact

Failure mode:

- treating every forum card like automatic repo truth creates noisy sprint churn

## 2. Private Testing / Canary Boundary

Private testing surfaces exist so workflow changes can be rehearsed without polluting the public board.

Current governed intent:

- use private `feedback-testing` for sorting and display canary checks
- do not apply public planning assumptions to canaries by default
- private canaries do not require the same completion-review path by default

Private testing may:

- rehearse tag, sort, display, and card-format changes
- validate low-risk operator workflow changes
- prove structure before public board hygiene changes

Private testing may not:

- silently change public workflow truth
- bypass review and promotion boundaries
- masquerade as shipped public user-facing evidence

Rule:

- private canaries are rehearsal surfaces, not default public workflow truth

Failure mode:

- teams use canary behavior as if public workflow already adopted it

## 3. Completion Review Requirement

Completion Review is the post-completion boundary for public Fitness app cards marked `Fixed` or `Completed`.

Canonical intent:

- `Ready for Fawxzzy Review` may be an optional pre-work scope gate
- Completion Review is a required post-completion queue for public Fitness app cards
- success reaction and board hygiene follow approved completion

Completion review proves:

- the shipped work actually satisfies the card
- the public board can advance to a resolved state safely
- the card is not being marked done from thread churn alone

Rule:

- completion review is required before public shipped-card closure is treated as final workflow truth

Pattern:

- shipped work -> completion-review queue -> approved review -> resolved-state hygiene

Failure mode:

- cards get marked fixed/completed from implementation optimism instead of reviewed closure

## 4. `#updates` Post Boundary

`#updates` is a public release-announcement boundary, not a mutation log.

Canonical update flow:

1. production deployment event is observed
2. Fitness creates or refreshes a bounded update draft
3. admin reviews via `/update-latest`
4. admin publishes via `/update-publish`
5. Discord receives curated user-facing copy

Rules:

- feedback-card updates do not automatically post to the updates channel
- one shipped item gets one appropriate public format
- shipped-card promotion uses the short `Update:` format with `Report ID`
- broad release summaries remain separate and curated

Rule:

- no Discord post before proof

Failure mode:

- mixing thread-audit copy, broad release-summary copy, and card-promotion copy for the same shipped item creates duplicate and confusing public history

## 5. Release-Ledger Dependency

Discord updates depend on shipped evidence; they do not create it.

Current strong dependency:

- Fitness production deploys should record a release ledger entry
- update drafts consume bounded deployment metadata
- curated public posts should align with shipped proof and ledger truth

This boundary exists so:

- public release narration stays tied to shipped evidence
- Discord copy does not outrun the actual release record
- public announcements stay downstream of verified deploy/release posture

Rule:

- release-ledger evidence and shipped proof are upstream of public update publication

Pattern:

- shipped proof -> release ledger -> bounded draft -> curated public post

Failure mode:

- Discord becomes the only remembered release history while durable shipped evidence is weak or missing

## 6. Bot Commands vs Panels Rule

Discord OS uses both commands and panels, but their roles must stay explicit.

User-facing surfaces:

- `/feedback`
- feedback panel `Submit`
- feedback panel `Add Update`
- feedback panel `Withdraw`

Staff/admin surfaces:

- `/feedback-status`
- `/feedback-completion-review`
- `/setup-feedback`
- `/update-latest`
- `/update-publish`
- `/update-skip`

Operator scripts:

- `npm run feedback:board:export`
- `npm run feedback:sync-forum-posts`
- `npm run feedback:sync-resolved-reactions`
- `npm run doctor:discord-community`

Rules:

- board export is an operator workflow, not a public Discord action
- commands and panels mutate bounded workflow state; they do not authorize implementation or deploy by themselves
- operator scripts may inspect, export, and reconcile, but should not silently widen public behavior

Failure mode:

- operators confuse a convenient command or panel with authority to skip review, proof, or export boundaries

## 7. Public / Product vs Operator / Admin Boundary

Discord OS must keep user-facing product surfaces separate from operator or admin control surfaces.

Public/product surfaces:

- feedback forum starter posts and threads
- curated `#updates` posts
- visible board tags and thread history
- user-facing modals and panels

Operator/admin surfaces:

- board export scripts
- completion-review controls
- update-draft review/publish controls
- community doctor and synchronization commands
- planning and reviewed-promotion workflows

Rule:

- only `Updates` and `Main` are loud channels; other Discord workflows should avoid broad pings by default

Failure mode:

- internal/operator workflow leaks into user-facing spaces and turns Discord into noisy admin theater

## 8. Discord OS Ownership Boundary

Discord OS is not a general stack-wide control plane. It is a community/workflow surface owned primarily by Fitness today.

Current ownership split:

- Fitness owns identity, Discord interactions, feedback board, update drafts, and public release-post mechanics
- Discord surfaces transport, present, and collect bounded user/admin actions
- ATLAS projects and records cross-repo consequences
- Playbook owns reusable governance doctrine after reviewed promotion

Rule:

- finish the operating system before adding another bot

Failure mode:

- stacking more Discord features on undocumented production lessons creates brittle automation and stale docs

## 9. Where ATLAS Stores Durable Truth

ATLAS stores reviewed internal truth, not raw Discord exhaust.

ATLAS should store:

- cross-repo workflow maps
- governance checkpoints
- convergence receipts
- lock decisions and validation posture
- reviewed summaries worth preserving beyond the owner repo

ATLAS should not store by default:

- every raw feedback card
- raw Discord payloads
- bot draft state
- full board copies as if root owned the board

Pattern:

- Discord operational signal -> reviewed export or receipt -> ATLAS durable summary

Failure mode:

- writing every Discord artifact into ATLAS creates duplicate task truth and obscures the real owner surface

## 10. Where Playbook Extracts Reusable Doctrine

Playbook becomes mandatory when Discord workflow lessons become reusable stack doctrine rather than app-specific operational details.

Strong extraction candidates:

- one-board reviewed-promotion rule
- no-Discord-post-before-proof doctrine
- shipped-card one-format-only rule
- public-channel vs operator-surface separation
- direct Discord-to-repo write prohibition
- release-proof-to-public-update dependency

Rule:

- reviewed promotion is required before Discord feedback becomes durable engineering truth

Pattern:

- Discord operational evidence -> reviewed export -> Playbook triage -> doctrine candidate

Failure mode:

- Discord habits stay trapped inside one app instead of becoming reusable governance

## 11. What Must Not Happen Before Proof / Deploy

The following are explicitly blocked in the canonical workflow:

- no public `#updates` publish before governed proof exists
- no broad release post from raw deploy metadata alone
- no auto-promotion of feedback cards into ATLAS truth
- no automatic GitHub or repo writes from raw Discord card state
- no deploy authority inferred from Discord workflow
- no `tmp` fallback for canonical proof or release truth

Rule:

- proof and reviewed promotion must precede publication and durable truth

## 12. User-Facing vs Internal-Only Classification

User-facing:

- feedback forum cards and visible thread history
- curated `#updates` posts
- user-facing panels and modals
- safe board tags, titles, and reactions

Internal-only:

- bounded database rows and draft metadata
- operator export artifacts
- completion-review queues and checklists
- ATLAS receipts and convergence docs
- Playbook doctrine candidates and notes
- operator doctor and sync outputs

Rule:

- user-facing surfaces should stay readable, curated, and low-noise; internal-only surfaces may stay operational and structured

Failure mode:

- raw internal workflow state leaks into public channels and makes the community surface feel like a back office

## Relationship To Existing Convergence Maps

This map is the Discord-facing counterpart to the release/deploy/update and proof-side handoff maps.

Joined chain:

1. feedback intake begins in Discord
2. reviewed exports and proof flow through repo and operator boundaries
3. release/deploy/update handoff governs public shipping
4. `#updates` remains downstream of proof and shipped evidence
5. ATLAS records reviewed durable truth
6. Playbook extracts reusable doctrine

That keeps Discord in the workflow without letting it become source truth for deploy, proof, or implementation.

## Remaining Gaps

- current Discord workflow reliability is strongest in Fitness, not yet generalized across other app/community lanes
- Discord update/release-ledger automation is not yet a shared stack contract outside Fitness
- broader Spotify Club or adjacent community doctrine is not yet fused into this convergence lane
- publication reliability and docs durability remain a later operational-hardening lane after this boundary map

## Validation

Validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

Expected interpretation for this package:

- docs-only Discord workflow boundary map
- no Discord post
- no bot change
- no deploy
