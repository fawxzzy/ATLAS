# Operating Model

## 2026-07-15 current capability override

Atlas root owns governance, markers, v1 contracts, and accepted receipts; `_stack` owns governed action routing, operator flows, and event normalization; Playbook owns doctrine and repo verification; root-owned Cortex surfaces provide advisory context/routing/synthesis; owner repos own product/code truth; DiscordOS is the one logical board/publication/readback writer; GitHub is remote/CI/review/release/security truth; Vercel is delivery/observability; Supabase is auth/persistence; Codex supplies bounded execution tasks; ATLAS MAIN routes standing command surfaces.

Runtime placement is explicit: Foundation is the hosted read-only portfolio,
DiscordOS is the hosted API/writer, Playbook Observer is the private loopback
cockpit, Lifeline is its intended local supervisor, `_stack` may later run one
bounded serialized scheduled sweep, and Cortex refreshes read models only on
accepted state or digest changes. See [Runtime Placement](16-runtime-placement.md).

Native desktop handoff creates a separate Codex transcript and receipts are the durable reverse handoff. Current manual evidence proves local/worktree/cloud tasks, deep links, follow-up steer/queue behavior, subagent threads, and task-scoped IDE context, but not the full Atlas callback loop. Atlas Control and its backend-neutral ledger, persistent workspace/browser leases, delivery event plane, historical task intelligence, and systematic cross-project promotion remain partial or **PROPOSED**. SQLite is a frozen proposal, not deployed truth. Current standing surfaces are ATLAS MAIN, existing Mazer, future Fitness after gates, with DiscordOS embedded.

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

## Standing Project Command Surfaces

The intended operator-facing command surfaces are long-lived governed
conversations:

- `00 Questions` is the pinned general-purpose conversation for questions, status,
  planning, architecture, and explicitly requested bounded work.
- `00 Authorization` handles genuine operator authority and external-evidence
  decisions. Repeated eligible low-risk approvals are learned under the
  canonical authorization policy.
- `00 Main` is the pinned anchor conversation. It is active during
  operational preparation and owns stack-wide
  architecture, governance, routing, receipts, and readiness decisions.
- `Fitness` is created when the operational-preparation closeout proves the
  Fitness resume gates below.
- The existing `Mazer` conversation is retained. When its resume gates pass,
  it receives a current Atlas context packet and resumes from its preserved
  checkpoint instead of being replaced by a new conversation.

DiscordOS is not a standing operator conversation. It remains the single
logical board and Discord writer invoked by governed Fitness, Mazer, Atlas,
and Codex task workflows.

Creating `Fitness` and refreshing `Mazer` are readiness-triggered bootstrap
actions, not evidence that the projects were already ready. The
operational-preparation closeout must prove:

- Atlas root truth and the canonical workspace writer are healthy
- the Work-to-Codex-to-`_stack` execution and receipt loop passes
- runtime policy is explicit and receipted
- DiscordOS board inspection, mutation, idempotency, sync/readback, and
  appropriate Updates-channel publication pass a governed canary
- each project has a current component manifest, Playbook profile, repo
  context packet, and board snapshot
- Mazer has a reconstructible live preview and browser workspace
- Fitness validation is healthy and direct Discord writes no longer bypass
  the DiscordOS single-writer boundary

After those gates pass, create the Work conversation named `Fitness` and send
the existing `Mazer` conversation a current context-and-resume packet. Each
conversation owns project intent and review; each bounded outcome still
receives a separate Codex task through `_stack`.

`00 Questions`, `00 Authorization`, `00 Main`, `Fitness`, and `Mazer` are durable command surfaces. Bounded
execution tasks are disposable work surfaces: after a terminal result is
accepted and its receipt is durable, archive the task to keep the workstation
clean. Never archive an active or intentionally persistent owner conversation.

When canonical Atlas truth requires a stable workspace-registration window,
`00 Main` may explicitly pause an owner conversation at its nearest safe
checkpoint. The pause receipt must preserve branches, worktrees, uncommitted
files, servers, board state, and the exact resume action. Resume requires an
explicit message from `00 Main` after the serialized root window closes.

Every substantive conversation turn persists a compact secret-free checkpoint
under `runtime/atlas/thread-context/`. Every cross-thread message explicitly
labels whether it is a handoff, whether a response is expected, its return
target, and its wake condition.

At the start and closeout of every governed owner-lane task, the workflow must
inspect the relevant DiscordOS project board and then create, update, move,
archive, or remove cards only when current board truth and task evidence
justify the action. Appropriate completions, releases, deployments, and other
policy-selected events publish through the event-specific Updates-channel
format. Routine internal steps must not turn the Updates channel into a
firehose.

## Atlas Reopen Sequence

Operational preparation remains the active Atlas lane. When its readiness
gates pass, the operator must receive an explicit notification that the Atlas
Clean and Re-sync marker cluster is ready to resume before that cluster begins.

The marker cluster then runs as one serialized execution, reconciliation, and
ratchet sequence. Historical `100%` closeouts remain historical; current marker
movement requires current execution and proof. When the cluster is complete,
the operator must receive a second explicit notification that general Atlas
systems work is reopened.

The cluster includes a major two-pass full-system re-evaluation lane. It begins
at `0%`, reaches `50%` only after an exhaustive opening audit of every governed
Atlas component and integration, and reaches `100%` only after a closing audit
rechecks the full system against the completed work. Work discovered by either
audit becomes a separately measured lane; it is not hidden inside the
re-evaluation percentage.

The closing audit is also the mandatory pre-development gate. It runs only
after operational preparation and the resumed Clean and Re-sync marker cluster
are terminal. It must review all completed work and every governed component,
repository, integration, control plane, contract, receipt path, board workflow,
document surface, and source-of-truth boundary. It must actively search for
gaps, missing work, stale assumptions, new ideas, additions, updates, risks,
quality problems, dependency conflicts, and cross-system synergies.

Every discovery receives an explicit disposition. Preparatory gaps become new
percentage markers with accepted denominators and must close before the
development gate opens. Development-scope discoveries become measured backlog
lanes, but may not start early merely because they were found by the audit. The
closing audit itself moves from `50%` to `100%` only after its evidence is
accepted; wording changes or child-lane progress contribute zero points.

General Atlas systems work includes Atlas root, `_stack`, Playbook, Cortex,
Foundation, Lifeline, DiscordOS platform work, Atlas Contracts, governance,
automation, knowledge promotion, delivery events, and other governed Atlas
software or projects. It excludes Fitness and Mazer owner-repository feature
work, which resumes through the separate `Fitness` and `Mazer` Work
conversations.

That exclusion does not create silos. Shared rules, contracts, components,
failure modes, automation, evidence formats, deployment patterns, DiscordOS
capabilities, and infrastructure improvements discovered in any lane should be
promoted into the correct Atlas-owned surface when they are genuinely reusable.
Atlas coordinates the overlap; it does not absorb owner-project implementation.

## Post-Preparation Development Program

After the pre-development gate passes, Atlas enters a distinct software and
platform development program. Its target scope is the completion and deep
integration of Lifeline, Foundation, Cortex, `_stack`, DiscordOS, Playbook,
Atlas root, Atlas Contracts, Atlas Control, the Atlas Book, and every governed
cross-system seam. This phase is not a continuation of operational cleanup; it
is product and platform engineering against separately ratified development
markers.

The development program must:

- finish each Atlas-owned system against explicit owner contracts and executable
  definitions of done
- wire the systems into one coherent Atlas control plane without collapsing
  owner boundaries or creating duplicate sources of truth
- replace ChatGPT- and Codex-dependent capabilities with Cortex-owned
  capabilities to the highest degree that current evidence, safety, quality,
  cost, and maintainability justify
- keep public callback and durable state capabilities on their proven hosted
  owners while keeping Lifeline local and Foundation read-only; any future
  replacement of Vercel or Supabase requires explicit parity, reliability,
  security, observability, migration, rollback, and cost evidence rather than
  shifting authority into Lifeline or Foundation by default
- preserve local-first operation, GitHub-backed collaboration and recovery, and
  deterministic receipts across every migration
- keep Fitness and Mazer feature development in their standing owner tasks while
  promoting reusable contracts, patterns, infrastructure, and failure modes into
  Atlas through evidence-backed convergence paths

No external platform or model dependency is removed merely to satisfy a vision
statement. Each replacement is a bounded, reversible migration lane with a
baseline, parity contract, cutover proof, rollback plan, and post-cutover audit.

## Cloud And Delivery Control Planes

Atlas remains local-first, but GitHub is a first-class cloud collaboration,
backup, and delivery control plane alongside Vercel and Supabase. Governed
health must include repository inventory, local/remote parity, default and
active branches, pull requests, Actions, releases, dependency and security
signals, stale-resource cleanup, and the relationship between commits, pushes,
merges, deployments, cards, receipts, and Updates-channel publications.

`_stack` produces verified Git and delivery facts. Atlas records their durable
identity and policy consequence. DiscordOS renders policy-selected status and
alerts; it does not infer GitHub truth from chat prose. Cleanup of old branches,
worktrees, runs, releases, or other remote state remains evidence-based and
must preserve active work.

## Execution And Projection Integrity

- The desktop app and the governed `_stack` Codex executable may support
  different model catalogs. Resolve capabilities before launch, never request
  an unsupported model, and receipt the requested model, resolved model,
  reasoning, speed, permissions, and Codex version.
- Canonical workspace workers may edit only admitted paths. They must not stage
  or commit; the parent `_stack` runner owns exact staging, verification,
  spec-to-diff, commit creation, and landing.
- Generated truth projections must declare snapshot semantics. A projection
  generated from a pre-commit head must record that source explicitly or avoid
  treating its own projection commit as immediate drift. Do not create endless
  refresh commits to chase self-referential metadata.

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
- keep one root writer and one writer per owner-repository or external-resource conflict group; distinct scopes may execute concurrently, with read-only scouts admitted only when their claims do not collide
- schedule every canonically authorized READY standing packet into the earliest dependency-satisfied conflict-free wave; a blocked lane suppresses only its writer scope
- when no READY packet exists, permit one bounded selector to admit owner-local preparation only through `standing_local_source_preparation`: immutable parent, exact relative files, one isolated worktree, unstaged local mode, and publication held
- treat heartbeats as interruption recovery, never as the cadence engine; terminal receipts trigger immediate lease release and next-wave selection
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
