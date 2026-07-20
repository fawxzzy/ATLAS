# ATLAS workflow architecture audit — 2026-07-20

## Result

ATLAS now has a versioned logical-role contract, generated human view, replaceable runtime-ID registry, lifecycle/topology model, canonical prompt fragments, no-archive recovery command, and focused failure fixtures. The current-manifest live confirmation (`sha256:15c424327f2fa88de3d00db46b6bbb655e76aae769bc4b7d048ffba3b27e6b8a`) discovered and reused all 13 declared standing role IDs with `0` missing, `0` duplicate, `0` create, and `0` mutations.

Live recovery is **not archive-ready**. The isolated Codex app-server can prove persisted thread identity, title, cwd, and archive listing, but it cannot prove desktop active/idle status or read/mutate pin state. All 13 roles therefore remain `DEGRADED`; a live apply fails closed before any task action. Fixture-safe create, partial-create retention, retry, idempotence, and no-duplicate behavior are proven.

ATLAS MAIN remains the authority sink. The workflow architect is a root-contract writer only. The canonical checkout (local-only Windows path observed during this run: `C:\ATLAS`), the held duplicate worktree, the app-owned shell, owner repositories, standing tasks, Architect epochs, automations, providers, production, boards, Discord, and live data were not mutated. The only task lifecycle mutation was the separately authorized archive of the obsolete coordination/bootstrap task after durable persistence and readback.

## Continuation delta

- Eight older runtimes whose bootstrap prose claimed standing status are now explicitly inventoried as `HELD` unbound claims. None is silently recreated, discarded, archived, or promoted into the required-role catalog.
- The canonical profile resolves DiscordOS as an embedded service; the older GitHub Control Plane is a preserved predecessor claimant to the admitted release control plane; Atlas Control, Clean & Re-sync, Playbook & Atlas Book, Atlas Runtime, Atlas Development, and AI Model Routing remain non-admitted historical program surfaces pending any future explicit role decision.
- Zac answered `ATLAS-WORKFLOW-MAN-001` through `003`. Digest-complete supersession envelopes were retained by ATLAS INBOX; the durable decision registry suppresses repetition while preserving `NOT_STARTED` execution truth.
- ATLAS INBOX rejected two incomplete answer routes: first for missing event payload digests, then for missing source thread ID/host/title. The envelope schema and validator now require source runtime identity and recompute the canonical payload digest instead of checking only its shape.
- The obsolete coordination/bootstrap task `019f7ded-cdb6-7d40-a102-74a70326d81c` was archived under exact user authority only after `ATLAS-WORKFLOW-BOOTSTRAP-CONTINUITY-HANDOFF.v1.json` validated. Independent app-server readback returned `archived=true`; no standing task or Architect epoch was archived.

## Evidence and inventory denominator

Evidence was reconciled across:

- root governance, canonical workflow profile, `stack.yaml`, and `README-STACK.md`;
- existing architecture, event, session, Atlas Book, program, runtime-placement, and contract documents;
- `_stack` operator scripts and package commands through read-only canonical-child inspection;
- Codex task-tool list/read results, local session and archived-session filenames, current role bootstrap prompts, and two heartbeat automation definitions;
- generated current Codex app-server schemas for thread list/read/start/resume/archive/unarchive/title and turn start;
- live app-server discovery of both archived and non-archived sessions;
- the runtime-rebind, worktree-admission, collision-stop, and source-preservation receipts for this role.

Inventory result:

- 13 required standing logical roles.
- 10 embedded/non-standing components or automations.
- 25 typed logical edges across control, event, decision, notification, owner, proof, and recovery relationships.
- 8 preserved unbound runtime claims, each `HELD` with no lifecycle authority.
- Older exact-title Fitness and Mazer chats are historical residue because they predate the accepted standing epoch and carry no stable standing-role marker.
- Two later `ATLAS MAIN` work-mode mirrors are preserved as explicitly non-accepted related epochs; neither replaces the original authority sink.
- DiscordOS is modeled as an embedded sole board-writer service. Its historical coordination runtimes do not make it a required standing conversation.
- Bounded implementation, review, recovery, and scout tasks are excluded unless durable evidence admits them as a standing role.

## Current role reconciliation

| Role | Runtime epoch | Live recovery result | Reason |
|---|---|---|---|
| ATLAS MAIN | `019f52d9-7667-72a3-a5f7-9c0613aedd8f` | `DEGRADED` | Persisted unique accepted epoch; desktop activity and pin are not app-server-readable. |
| ATLAS INBOX | `019f7de0-3e1d-7433-a760-a9b724174ab6` | `DEGRADED` | Unique persisted queue and successful route evidence; activity/pin unproven. |
| ATLAS WORKFLOW ARCHITECT | `019f7df6-8521-7292-a012-297208fce120` | `DEGRADED` | Runtime rebind and isolated lane accepted; activity/pin unproven through command adapter. |
| ATLAS PR, CI & Release Control Plane | `019f79ac-bd85-7952-8935-58dfbb77aa20` | `DEGRADED` | Unique persisted control plane; activity/pin unproven. |
| FAWXZZY QUESTIONS | `019f75ca-d9c7-7941-b73f-fb06ff2a0459` | `DEGRADED` | Unique persisted analysis surface; activity/pin unproven. |
| MANUAL MESSAGES | `019f70b7-fad4-74d2-90e3-e5f34c6fab06` | `DEGRADED` | Current manual-routing adoption exists; early notification prose is superseded, activity/pin unproven. |
| AI QUESTIONS | `019f79de-76cd-7062-9d8b-1b9f5fd6a8ba` | `DEGRADED` | Unique persisted research intake; activity/pin unproven. |
| FAWXZZY MESSAGES | `019f58c4-6d0b-7dc0-a4e3-9f6335f381e1` | `DEGRADED` | Later notification epoch selected; older epoch retained, archive/pin/activity unproven. |
| Fitness | `019f58c4-4a9e-7af3-bb3e-06e199884027` | `DEGRADED` | Current standing epoch reused; older same-title chats are historical, activity/pin unproven. |
| Mazer | `019f61a0-6b80-7913-b479-f75f2a8a5b77` | `DEGRADED` | Explicit full-access replacement selected; preserved checkpoint retained, activity/pin unproven. |
| Socials OS | `019f62b0-6fbe-79f0-9c47-a0942feb0825` | `DEGRADED` | Unique current owner epoch; activity/pin unproven by isolated adapter. |
| FawxzzyWeb | `019f7614-e612-77d0-b99b-ed1b0d277d1d` | `DEGRADED` | Current owner epoch selected; earlier owner epoch retained, activity/pin unproven. |
| FawxzzyPlatform — Supabase Migration | `019f6dad-2cc3-7551-a47d-4b8c912c51ef` | `DEGRADED` | Original epoch remained live in task-tool evidence while declared replacement was not loadable; accepted supersession is unresolved. |

The clean held worktree `workflow-architect-20260720` is `HELD`, not a second role runtime. The workflow command never selects or mutates it.

## Architecture scorecard

Scores are 1 (unsafe/implicit) through 5 (explicit/proven). “After” includes this packet but does not award live proof that is still unavailable.

| Area | Before | After | Evidence and remaining gap |
|---|---:|---:|---|
| Role clarity / separation | 2 | 4 | Prior three-chat document conflicted with evolved live surfaces. Stable IDs, purpose, authority, prohibitions, routes, and component separation are now canonical. Runtime contract adoption remains pending. |
| Single-writer / duplicate risk | 3 | 4 | Governance existed but was distributed. Manifest and recovery preflight fail closed on role, lease, branch, worktree, and cwd collisions. Live lease-source discovery is still incomplete. |
| Event routing / retry / dedupe | 3 | 4 | Inbox routing, event IDs, digests, acknowledgements, and supersession are unified. Several physical ledgers/queues remain separately owned. |
| Manual-decision latency / fan-out | 4 | 4 | Stable question governance is strong. Three answers are now durable and retained by Inbox; Main route acknowledgement and expiry automation are not centrally observable. |
| Context growth / token cost | 2 | 3 | Canonical baseline plus role overlays remove repeated authority prose. Exact context budgets and rollover thresholds are not yet policy. |
| Boot / restart / partial failure | 2 | 4 | Deterministic boot phases, no-archive command, partial-create retention, and retry fixtures are landed. Live create is held on pin/activity readback. |
| Observability / health / stale state | 2 | 3 | One plan and registry now reconcile every role. Desktop pin/activity, automation, lease, and component health are not available from one adapter. |
| Standing vs bounded lifecycle | 2 | 4 | Separate state machines and admission/archive gates are canonical. Historical epochs still need explicit lifecycle acceptance. |
| Heartbeat usefulness / polling | 3 | 3 | Two bounded hourly automations use unchanged-state suppression. Logical-role target rebinding and duplicate-schedule proof remain manual. |
| Security / authority boundaries | 4 | 5 | Apply requires exact manifest/plan acceptance, defaults no-archive, and preflights unsupported operations before mutation. Provider/production/owner restrictions remain explicit. |
| Cortex / Playbook extensibility | 3 | 4 | Both are embedded contract consumers, not premature replacements. Event adapters and activation acceptance remain future work. |

## Ranked improvement backlog

| Rank | Change | Impact | Migration risk | Dependencies | Reversibility | Authority | State |
|---:|---|---|---|---|---|---|---|
| 1 | Deterministic desktop task-status and pin adapter | Critical | Medium | Codex desktop/app API | High | `MANUAL_REQUIRED` | Answered: live apply deferred until adapter exists |
| 2 | Adopt recovery behind the existing `_stack` command surface | High | Low | `_stack` owner change/review | High | `MANUAL_REQUIRED` | Answered: separate bounded owner packet admitted, not yet authorized for edits |
| 3 | Accept standing runtime supersession/lifecycle disposition | High | High | Ranks 1–2, zero pending routes | Medium | `MANUAL_REQUIRED` | Answered: lifecycle disposition deferred |
| 4 | Canonical manifest + live-ID separation + generated view | Critical | Low | None | High | `AUTO_ALLOWED` | Implemented |
| 5 | No-archive idempotent recovery planner and failure fixtures | Critical | Low | Rank 4 | High | `AUTO_ALLOWED` | Implemented; live apply held |
| 6 | Normalize isolated app-server `notLoaded` and historical-title semantics | High | Low | Live readback evidence | High | `AUTO_ALLOWED` | Implemented |
| 7 | Consolidated live lease/readiness projection | High | Medium | Canonical lease registry owner decision | High | `MANUAL_REQUIRED` | Deferred |
| 8 | Context budgets and automatic rollover candidate receipts | Medium | Medium | Operator policy thresholds | High | `MANUAL_REQUIRED` | Deferred |
| 9 | Heartbeat logical-role rebinding and duplicate-schedule audit | Medium | Medium | Automation mutation authority | High | `MANUAL_REQUIRED` | Deferred |
| 10 | Cortex/Playbook typed envelope adapters | Medium | Medium | Stable event/receipt adoption | High | `MANUAL_REQUIRED` for activation | Designed, deferred |

## Improvement records

### 1. Deterministic desktop task-status and pin adapter

- **Observed evidence:** App-server `thread/list` discovers all 13 persisted epochs but reports them `notLoaded` in the isolated process and exposes no pin field/method. Codex desktop tools can pin and report active/idle, but are not callable by the standalone root command.
- **Root cause:** Runtime inventory and desktop task-management capabilities are split across two APIs with different state semantics.
- **Affected contracts:** Health, safe-boundary proof, pin policy, create/repair, post-create readback, archive readiness.
- **Options considered:** (A) infer desktop state from app-server `notLoaded`; rejected as false. (B) ignore pin; rejected because standing-role pin is required. (C) add a deterministic desktop adapter or accepted receipt bridge; selected.
- **Selected recommendation:** Expose read-only desktop status/pin discovery and exact pin mutation through a versioned adapter, or persist a signed desktop receipt consumed by the command.
- **Why alternatives lose:** Inference can steer active work; skipping pin violates the standing-role contract; manual memory is not deterministic.
- **Migration risk:** Medium—incorrect state translation can create/steer duplicates.
- **Rollback:** Disable the adapter and return to app-server-only `DEGRADED`/fail-closed behavior.
- **Verification:** Healthy live dry-run, pin/readback round trip on a fixture/non-standing test role, active-target hold, repeat plan digest, zero duplicate/create on second run.
- **Authority:** `MANUAL_REQUIRED` because it changes task-management integration and is a prerequisite to live reconstruction acceptance.

### 2. `_stack` recovery wrapper adoption

- **Observed evidence:** `_stack` owns stack task/session commands; this packet could inspect but was forbidden to edit that owner repository. The root currently hosts the safe implementation under `ops/atlas`.
- **Root cause:** Required command ownership and the admitted root-only mutation boundary differ.
- **Affected contracts:** Operator discoverability, package scripts, task creation ownership, release/versioning.
- **Options considered:** (A) add a parallel root orchestration system; rejected. (B) implement nothing; rejected because recovery proof was required. (C) land the root engine and later add a thin `_stack` wrapper; selected.
- **Selected recommendation:** Add one `_stack` command that invokes the versioned root engine, passes explicit workdir/acceptance paths, and preserves `_stack` as operator owner.
- **Why alternatives lose:** Parallel orchestration duplicates ownership; deferral alone leaves no recovery artifact.
- **Migration risk:** Low if the wrapper is thin and read-only by default.
- **Rollback:** Remove the wrapper; the root engine and manifest remain usable.
- **Verification:** `_stack` unit/integration test, dry-run output byte parity with direct root invocation, package help text, no live mutation.
- **Authority:** `MANUAL_REQUIRED` because owner-repository edits were explicitly prohibited in this packet.

### 3. Standing runtime supersession and lifecycle disposition

- **Observed evidence:** Mazer, FAWXZZY MESSAGES, FawxzzyWeb, workflow architect, and Platform have predecessor/replacement evidence. Platform has a declared replacement but the original was still live; two ATLAS MAIN work-mode mirrors remain preserved; older exact-title chats exist.
- **Root cause:** Runtime rollover occurred faster than durable role/epoch acceptance and archive receipts.
- **Affected contracts:** Current binding, route targets, pending event ownership, archive eligibility, automation targets.
- **Options considered:** (A) select newest ID; rejected. (B) archive all older titles; rejected. (C) record relationships, retain all, and obtain explicit per-role acceptance; selected.
- **Selected recommendation:** After rank 1 is available, reconcile each affected role's pending events and routes, accept one epoch, mark predecessors only `ARCHIVE_ELIGIBLE`, and request archive separately.
- **Why alternatives lose:** Age/title do not prove authority; mass archival can strand receipts and active work.
- **Migration risk:** High due to task lifecycle and route fan-out.
- **Rollback:** Keep all epochs unarchived and restore the last accepted registry binding.
- **Verification:** Complete non-archived/archived discovery, zero pending routes, successor prompt/route readback, ATLAS MAIN acceptance, post-action readback.
- **Authority:** `MANUAL_REQUIRED` for lifecycle selection and any archive/rename/pin action.

### 4. Canonical manifest and generated view

- **Observed evidence:** Existing workflow documentation described only three standing conversations while current governance admitted additional queues, control planes, owners, and a platform coordinator.
- **Root cause:** Human prose and runtime evolution had no common stable-role source.
- **Affected contracts:** Role identity, prompts, topology, boot, lifecycle, health, recovery.
- **Options considered:** (A) update prose only; rejected. (B) encode opaque thread IDs as primary keys; rejected. (C) one machine manifest plus generated view and separate live registry; selected.
- **Selected recommendation:** Keep `ATLAS-WORKFLOW-MANIFEST.v1.json` canonical; generate the human view; refresh runtime IDs separately.
- **Why alternatives lose:** Dual manual sources drift; opaque IDs make rollover unrecoverable.
- **Migration risk:** Low—additive root artifacts.
- **Rollback:** Revert the packet; existing docs remain unchanged.
- **Verification:** Schema and semantic validation, prompt markers, generated-view byte check, exact role/edge counts.
- **Authority:** `AUTO_ALLOWED`; implemented locally and reversibly.

### 5. No-archive recovery planner and failure fixtures

- **Observed evidence:** Worktree collision, missing rollout, stale ID, duplicate title, active-writer, and partial-create failure modes were all observed or explicitly required.
- **Root cause:** No deterministic role reconciliation or retry contract existed.
- **Affected contracts:** Discovery, create/reuse/repair, dedupe, rollback, registry refresh, health reporting.
- **Options considered:** (A) manual recreation from chat; rejected. (B) always create; rejected. (C) manifest-driven plan with acceptance-gated apply and fixture adapter; selected.
- **Selected recommendation:** Retain the command and focused fixtures; do not enable live create until capability proof closes.
- **Why alternatives lose:** Manual recollection is non-repeatable; create-first generates duplicates.
- **Migration risk:** Low while live apply remains gated.
- **Rollback:** Stop invoking the command; no live state was mutated.
- **Verification:** 14 focused tests, fixture apply/retry, exact live dry-run, deterministic plan digest, and default zero-archive capability.
- **Authority:** `AUTO_ALLOWED`; implemented.

### 6. `notLoaded` and historical-title normalization

- **Observed evidence:** A fresh app-server reported every desktop task `notLoaded`; exact-title search found pre-standing Fitness/Mazer chats and later Main work-mode mirrors.
- **Root cause:** App-server load state was incorrectly treated as desktop inactivity, and title matching lacked epoch chronology/relationship evidence.
- **Affected contracts:** Safe boundary, duplicate detection, repair planning, live health.
- **Options considered:** (A) resume all; rejected. (B) ignore all same-title sessions; rejected. (C) preserve activity as unknown, ignore only older unmarked residue, and require newer relationships in registry; selected.
- **Selected recommendation:** Keep the normalized semantics and stable-marker preference.
- **Why alternatives lose:** Resume-all can interfere with active work; ignore-all can miss real replacement collisions.
- **Migration risk:** Low.
- **Rollback:** Revert to all-unknown fail-closed discovery.
- **Verification:** Live result changed from false duplicates/resume plans to 13 reused, zero duplicate/create, with safe-boundary and pin still explicit.
- **Authority:** `AUTO_ALLOWED`; implemented.

### 7. Consolidated live lease/readiness projection

- **Observed evidence:** Lease schema and single-writer doctrine exist, but the standalone recovery command has no canonical denominator for current root/owner leases, worktree claims, and safe boundaries.
- **Root cause:** Lease evidence is distributed across runtime files, tasks, Git worktrees, and owner tools.
- **Affected contracts:** Preflight, active-writer collision, parallel boot, repair safety.
- **Options considered:** (A) scan every runtime directory heuristically; rejected. (B) trust task titles; rejected. (C) define one owner-produced lease projection consumed read-only; selected.
- **Selected recommendation:** Ratify a canonical lease/readiness projection with expiry and source receipts; consume it without moving ownership to root.
- **Why alternatives lose:** Heuristics create stale false positives/negatives; title state is not a lease.
- **Migration risk:** Medium due to source-of-truth ownership.
- **Rollback:** Stop consuming the projection and fail closed on UNKNOWN.
- **Verification:** Duplicate lease fixtures, expired lease handling, worktree/branch collision tests, owner/root readback.
- **Authority:** `MANUAL_REQUIRED` because source-of-truth ownership must be chosen.

### 8. Context budgets and rollover receipts

- **Observed evidence:** Long standing prompts repeat authority prose; work-mode mirrors and missing rollouts show continuity pressure. Baseline-plus-overlay reduces repetition but has no hard rollover trigger.
- **Root cause:** Context/compaction policy is advisory rather than measured and role-specific.
- **Affected contracts:** Prompt size, token cost, continuity, successor timing, archive eligibility.
- **Options considered:** (A) fixed universal token threshold; rejected. (B) rely on compaction only; rejected. (C) measured role budgets with warning/rollover candidate receipts; selected.
- **Selected recommendation:** Add advisory thresholds per role, persist a continuity digest before rollover, and require successor proof before lifecycle change.
- **Why alternatives lose:** Universal limits ignore role workload; compaction alone does not prove reconstructibility.
- **Migration risk:** Medium if thresholds cause churn.
- **Rollback:** Disable automatic candidate emission; retain manual rollover.
- **Verification:** simulated context-growth fixtures, no duplicate successor, digest/readback parity, token-cost trend.
- **Authority:** `MANUAL_REQUIRED` because threshold policy materially changes lifecycle frequency.

### 9. Heartbeat logical-role rebinding

- **Observed evidence:** Two hourly automations target current opaque IDs and correctly suppress unchanged runs; rollover would stale those targets.
- **Root cause:** Automation targets are runtime IDs rather than resolved logical roles.
- **Affected contracts:** interruption recovery, PR watch, duplicate schedules, stale-task risk.
- **Options considered:** (A) leave IDs static; rejected long term. (B) poll all roles; rejected. (C) one logical-role resolver and duplicate-schedule audit; selected.
- **Selected recommendation:** On accepted rollover, rebind once from registry, prove one active automation, and record a route receipt.
- **Why alternatives lose:** Static IDs decay; broad polling increases cost/noise.
- **Migration risk:** Medium because automation mutations can wake work.
- **Rollback:** Restore prior target and disable the replacement schedule.
- **Verification:** dry-run target diff, exactly-one schedule, unchanged-run suppression, old-target no-wake proof.
- **Authority:** `MANUAL_REQUIRED`; automation mutation was explicitly prohibited.

### 10. Cortex and Playbook typed envelope adapters

- **Observed evidence:** Cortex/Playbook are present as advisory/read-model systems; replacing working ATLAS routing now would be premature.
- **Root cause:** Their integration boundary is conceptual but not yet bound to the new role/envelope manifest.
- **Affected contracts:** event intake, knowledge candidates, advisory read models, future automation.
- **Options considered:** (A) replace Atlas/Playbook now; rejected. (B) leave prose-only seams; rejected. (C) add typed read-only adapters after event contract adoption; selected.
- **Selected recommendation:** Consume accepted workflow envelopes and emit advisory receipts only; activation remains a separate gate.
- **Why alternatives lose:** Replacement risks authority regression; prose-only integration cannot be validated.
- **Migration risk:** Medium.
- **Rollback:** Disable adapters; canonical Atlas sources remain unchanged.
- **Verification:** schema fixtures, replay determinism, no mutation authority, read-model freshness/readback.
- **Authority:** Design is `AUTO_ALLOWED`; activation/writer changes are `MANUAL_REQUIRED`. Deferred to avoid premature scope expansion.

## Implemented safe optimizations

- Stable logical role IDs separated from runtime thread IDs.
- Versioned task catalog with authority, prohibitions, routes, runtime floors, cwd/project locators, lifecycle, pin/archive, health, wake, and terminal rules.
- Typed logical topology and serialized/parallel boot graph.
- Unified event/receipt/manual/route/ack/supersession envelope.
- Required source thread ID/host/title plus semantic canonical payload-digest verification for every envelope.
- Durable answered-decision registry with repeat suppression and separate transport/execution truth.
- Eight explicit unbound runtime claims so historical standing prose cannot trigger silent creation or cleanup.
- Baseline-plus-role prompt composition to reduce duplicated authority context.
- No-archive, acceptance-gated recovery command with app-server and fixture adapters.
- Exact duplicate, stale-ID, missing, active-writer, partial-create, retry, and unknown-state handling.
- Dependency-free schema/semantic validation and generated human view.
- Correct Windows npm shim startup, safe app-server `notLoaded` semantics, and historical-title residue handling.
- README and operator runbook entry points.

## Verification truth

Passed:

- Manifest/runtime/envelope/plan schema and semantic validation.
- Generated human view byte check.
- 14 focused Python tests.
- Fixture apply creates exactly one missing role; repeat dry-run creates zero.
- Fixture partial-create retains one runtime; retry repairs it without duplication.
- Current-manifest live app-server confirmation: 13 reused, 0 missing, 0 duplicate, 0 create, 0 mutation, 8 preserved unbound claims, terminal `DEGRADED`, plan digest `sha256:15c424327f2fa88de3d00db46b6bbb655e76aae769bc4b7d048ffba3b27e6b8a`.

Not run or not proven:

- Whole-stack validator completion in this isolated source-only checkout: it stopped before validation because registered child path `repos/_stack` is absent. The workflow-specific contract validator remains green.
- Live standing-role create, resume, unarchive, rename, pin, bootstrap, or archive. Only the separately authorized bounded bootstrap-source archive/readback was performed.
- Desktop pin readback and active/idle safe-boundary readback from the standalone command.
- Live interconnection/bootstrap receipt round trip for a newly created standing role.
- `_stack` wrapper adoption.
- Automation rebinding or lifecycle cleanup.
- Provider, production, owner-repository, board, Discord, or live-data behavior.

## Archive-readiness assessment

`NOT PROVEN`.

The durable reconstruction contract, safe fixture creation/retry, deterministic live discovery, no-duplicate reconciliation, failure rollback, answered-decision retention, historical-claim preservation, and one exact bounded bootstrap archival/readback are proven. Live connection/readback for reconstructed standing roles is incomplete because pin and desktop safe-boundary state are unavailable to the command, and no independent live reconstruction acceptance exists. Existing standing tasks must remain unarchived.
