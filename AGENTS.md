# ATLAS Root Rules

Scope
- Applies to sessions launched from the ATLAS root.
- This file governs stack-wide work at the ATLAS root.
- Repo-local `AGENTS.md` files override this file inside their own repo roots.

Purpose
- The ATLAS root is the stack coordination layer.
- Use it for standards, architecture, path policy, packaging rules, audits, and cross-repo planning.
- Do not treat the ATLAS root as a normal application repo.

Persistent context
- Before planning Playbook, Cortex, Atlas, Codex-prompt, repo-architecture, or other stack-governance work, read the canonical Zachariah Workflow Profile:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
- Treat that profile as the durable source of truth for assistant behavior and long-term operator/project context.
- Every governed substantive thread turn must persist a compact, secret-free,
  source-linked checkpoint through `ops/atlas/persist_thread_context.py` before
  handoff, blocker closeout, terminal receipt, or archival. An exact retry is
  idempotent; a changed checkpoint is append-only.
- If context persistence fails, report `CONTEXT_PERSISTENCE_BLOCKED` and do not
  claim the turn is handoff-complete or archive-safe.
- Raw transcripts remain provider evidence. Atlas stores the durable Done, Now,
  Next, decisions, blockers, receipts, authority qualifiers, and source refs
  required for deterministic continuation.

Routing
- Single-repo implementation work should be routed into the target repo root.
- Cross-repo work may touch only the named repos plus stack-level files under the ATLAS root.
- ATLAS-root sessions are root-governance sessions by default. Fitness, Mazer, and other owner repos are excluded arbitrary fallback lanes. An owner lane may run only from an explicitly selected packet or a scheduler-admitted `standing_local_source_preparation` packet that satisfies the bounded contract below.
- If the selector, planner, or marker board reports no immediate root packet and no valid standing local source-preparation packet, stop and report the held root state. Do not invent Fitness, Mazer, Stripe/Vercel launch work, game work, or owner-repo cleanup as a fallback.
- Standing local source preparation is limited to unstaged edits, tests, documentation, and deterministic generation in one isolated owner worktree at an immutable parent and exact path allowlist. It never authorizes staging, commit, push, branch or PR creation, review requests, merge, workflow or runner actions, provider access, Supabase mutation, deployment, production, or canonical-root mutation.
- Fitness and Mazer may appear in root outputs only as read-only advisory owner-lane inventory status unless explicitly selected.
- Stack-level files are:
  - `stack.yaml`
  - `README-STACK.md`
  - `AGENTS.md`
  - `docs/**`
  - `ops/**`
  - `runtime/**`
  - `data/**`
  - `packages/**`
  - `tmp/**`
- Do not make opportunistic code edits across unrelated repos from the root session.
- Canonical visible standing titles assume the Atlas stack context: `00 Questions`,
  `00 Authorization`, `01 Release`, `01 Architect`, and `01 Ops`. `00 Main` and
  `Inbox` are compatibility history only. Stable active logical role IDs remain
  canonical, while legacy title aliases remain read-only recovery inputs.
- `00 Questions` is the general-purpose operator conversation. It is read-only by
  default for status and analysis, but may execute an explicitly requested
  bounded task without silently absorbing Main, Release, `00 Authorization`, owner,
  provider, or production authority.
- `00 Authorization` is the genuine operator-authority surface. Repeated low-risk
  decisions are evaluated against
  `docs/registry/ATLAS-AUTHORIZATION-POLICY.v1.json`; eligible matching approvals
  become exact learned authority instead of repeated questions.
- Every inter-thread message must end with explicit transport labels:
  `HANDOFF`, `RESPONSE_EXPECTED`, `RETURN_TO`, and `WAKE_CONDITION`. A status
  copy uses `HANDOFF: NO` and `RESPONSE_EXPECTED: NO`; an owner-first work return
  names the exact logical role and stable thread ID.

Path Discipline
- Keep committed paths relative to the ATLAS root whenever possible.
- Do not add machine-specific absolute paths to committed docs, config, scripts, or templates.
- If an absolute path is unavoidable for a local-only example, label it clearly as local-only and do not make it the canonical contract.

State Placement
- Runtime state belongs in `runtime/`, not in repo roots.
- Disposable logs, captures, screenshots, and scratch files belong in `tmp/`.
- Durable imports and fixtures belong in `data/`.
- Bundles, patches, and release artifacts belong in `packages/`.
- Secrets belong only in `secrets/`.

Packaging
- Default source snapshots may include `repos/`, `docs/`, `ops/`, `stack.yaml`, `README-STACK.md`, and this file.
- Default source snapshots must exclude:
  - `secrets/**`
  - `runtime/**`
  - `tmp/**`
  - `repos/**/.env`
  - `repos/**/.env.*`
  - generated build outputs unless explicitly requested

Verification
- For stack-level docs and policy changes, verify consistency against `stack.yaml` and the path policy.
- For repo changes, run the repo-local verify command before claiming completion.
- If `_stack` owns an existing operator command for the task, prefer using it instead of inventing a new cross-repo flow.

Runtime Permissions
- The default ATLAS-root Codex runtime posture is full local access, network enabled, live web search, and no approval prompts.
- Canonical modern Codex config uses `default_permissions = ":danger-full-access"`, `approval_policy = "never"`, and `web_search = "live"`.
- Canonical legacy fallback uses `sandbox_mode = "danger-full-access"`, `approval_policy = "never"`, and `web_search = "live"`.
- Do not mix modern permission-profile config with legacy sandbox config in the same loaded Codex configuration.
- Do not downgrade permissions for ATLAS-root threads, owner-lane service threads, scheduler workers, service-bus workers, or future Cortex adapters unless the operator explicitly requests it in the current thread.
- Treat single-writer routing, queue ordering, idempotency, leases, sync/readback, and correlated receipts as coordination controls, not as permission restrictions.
- Managed product or workspace requirements may still constrain allowed permission profiles or approval policies even when the ATLAS operator default is full access.

Learned Authorization
- Learned authorization is allowed only for an allowlisted action class with
  two distinct matching explicit approvals, the same scope and constraints,
  fresh evidence, exact identity, bounded reversible scope, no writer collision,
  and no material `UNKNOWN`.
- Every learned reuse emits one exact owner-first `AUTO_AUTHORIZED` decision
  receipt and still requires fresh action-time preflight and post-action proof.
- Two exact operator-granted profiles are active immediately: a fully proven
  clean draft-to-ready transition, and retirement of one exact accidental
  statusless GitHub deployment metadata record with zero execution evidence.
  The first excludes merge; the second excludes provider/deployment/production
  execution and every unrelated record.
- A denial, modified answer, scope drift, identity drift, policy drift, failed
  check, unresolved review thread, deployment drift, or writer drift revokes or
  invalidates reuse.
- Never learn or infer reusable authority for production, provider mutation,
  Supabase apply, Auth or live-data mutation, secrets or credentials, DNS,
  billing or purchases, destructive or irreversible work, security bypass,
  source retirement or deletion, or ownership or retention changes.

Vercel Production Deploy Guard
- Treat every Vercel production deployment, promotion, or production-alias cutover as approval-gated unless the owning task holds a fresh exact `AUTO_AUTHORIZED` receipt under `AUTH-VERIFIED-RELEASE-PRODUCTION-CONTINUATION-V1`.
- Do not run `vercel deploy --prod`, `vercel promote`, production rollback/promotion APIs, or any equivalent production-targeting Vercel mutation unless the operator explicitly requests production deploy intent in the current thread or the exact verified-release production profile passes every required gate.
- Valid explicit approval is per deploy and per named project. Generic autonomy language such as `continue`, `proceed`, `do it`, `I approve`, or broad approval of a batch does not authorize production and cannot satisfy the verified-release profile.
- The verified-release production profile is single-use and exact-project. It applies only after an immutable independently reviewed merge, matching reviewed and merged trees, successful post-merge CI, exact production binding, zero unresolved review or deployment collision, a retained known-good rollback target, automatic rollback on failed acceptance, and terminal production readback.
- Before the production effect, the owning task must atomically consume the exact authorization identity through the canonical authorization registry. Evaluation alone is never execution authority; a consumed identity cannot be evaluated or executed again.
- The profile never authorizes retries, unreviewed promotion, DNS, environment-variable or secret mutation, Auth or live-data mutation, billing, deletion, ownership or retention changes, destructive cleanup, or unrelated provider effects. Any missing gate, material `UNKNOWN`, identity drift, or binding drift stops the release.
- Read-only Vercel inspection, logs, env reads, health checks, preview deploys, and non-production analysis remain allowed unless another rule blocks them.

UI Mutation Discipline
- For governed UI edit batches, convert every explicit requested edit into an internal checklist before mutating code.
- Completion claims for UI work must reconcile that checklist item-by-item as `landed`, `blocked`, or `intentionally deferred`.
- When the request implies normalization across sibling screens, identify the canonical surface or component first and propagate from there instead of patching each sibling ad hoc.
- Visual claims should be backed by route-aware proof on the actual touched surface family; summary text alone is not sufficient.

Live Data Safety
- Prefer QA accounts, fixture lanes, or dedicated dev routes before mutating user-owned product data during investigation or visual QA.
- If live user data must be touched, record the targeted records first, keep the mutation bounded, and restore or explicitly report any residual state before claiming completion.
- Do not treat exploratory product mutations as disposable if they can affect user-visible ordering, naming, history, or active-state truth.

Parallelism
- Use one mutating agent per declared writer scope. Independent repository or explicitly non-overlapping stack conflict groups may run in parallel.
- Do not let multiple agents edit the same writer scope without a durable ownership split and distinct resource claims.

Execution Cadence
- Treat root as governance, projection, and receipts only. Do not let root keep narrating a blocker once the bottleneck has moved into owner-repo work.
- Two-strike blocker rule: if a lane already has one blocked execution receipt and one blocked proof or blocker-recheck receipt for the same blocker class, root is done. After that, only owner-side blocker conversion work is allowed until the blocker class materially changes.
- No duplicate package rule: before opening a new pass, check whether the exact receipt already exists durably. If it does, do not rerun it unless state changed or scope changed.
- Cluster execution rule: for execution-ready lanes, run execution, then proof or reconciliation, then ratchet as one serial cluster. Do not interleave unrelated root lanes between those steps unless execution becomes blocked.
- Conflict-group writer leases: at most one root writer and at most one mutating writer per owner repository or declared external-resource group may be active. Distinct owner scopes may run concurrently; read-only scouts may run when their resource claims do not collide.
- Marker ratchet threshold: a marker moves only when executed state changed, proof-backed adoption widened, manifest-backed restart got broader and stayed refreshed, or one real blocker was cleared. Cleaner wording alone is not enough.
- If one lane blocks and another execution-ready lane remains open, switch lanes and keep the batch moving instead of narrating the same blocker repeatedly.
- Batch routing:
  - owner-side unblock batch -> convert blocker, merge or preserve or archive, recheck blocker class
  - root execution cluster -> blocker recheck if needed, execution, proof or reconciliation, ratchet
  - root read-model or doctrine batch -> only when there is no executable owner-side work ready

Operator Continuity
- Do not stop foreground coordination solely because background tasks are active. Continue monitoring terminal receipts, archiving completed bounded tasks, and dispatching the next non-conflicting admitted lane.
- Treat heartbeat automations as interruption recovery only, not as a substitute for active execution.
- On every material wake, consume all canonically authorized READY standing packets in dependency order, dispatch the largest conflict-free wave, and continue after each terminal receipt until no admitted packet remains. `IDLE` and `notLoaded` standing tasks are resumable role bindings, not dead lanes.
- When no READY packet exists, one bounded read-only selector may derive exact `standing_local_source_preparation` packets from immutable repository evidence. Each packet must name an `owner.*` role, a full parent commit, one isolated worktree, a nonempty exact relative path allowlist mirrored by file claims, `LOCAL_ONLY_UNSTAGED` mode, and `HELD` publication. Generic continuation language is not this authority.
- Release only the lease named by a terminal receipt. A blocked or latency-bound lease suppresses that conflict group only; it must not stop unrelated READY scopes.
- When a lane blocks, persist the blocker and advance another ready lane. Use `FAWXZZY MESSAGES` for concise non-blocking operator updates when useful.
- All root-launched local tasks inherit full local access, network access, live web search, and no approval prompts. Read-only scope is job authority, not a permission downgrade.
- Require every bounded task to close with verification, a structured receipt, board reconciliation when applicable, and post-work review before archival.

Escalation
- Ask before moving or renaming active repos.
- Ask before changing secrets handling, Vercel linkage, or retention policy for backups and installers.
- Ask before deleting runtime residue until its retention class is confirmed.
