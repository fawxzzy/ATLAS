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

Routing
- Single-repo implementation work should be routed into the target repo root.
- Cross-repo work may touch only the named repos plus stack-level files under the ATLAS root.
- ATLAS-root sessions are root-governance sessions by default. Fitness, Mazer, and other owner repos are excluded fallback lanes unless the operator explicitly selects an owner-lane packet by name.
- If the selector, planner, or marker board reports no immediate root packet, stop and report the held root state. Do not switch into Fitness, Mazer, Stripe/Vercel launch work, game work, or owner-repo cleanup as a fallback.
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
- Use one agent per repo or one non-overlapping stack file slice.
- Do not let multiple agents edit the same repo root without a clear ownership split.

Execution Cadence
- Treat root as governance, projection, and receipts only. Do not let root keep narrating a blocker once the bottleneck has moved into owner-repo work.
- Two-strike blocker rule: if a lane already has one blocked execution receipt and one blocked proof or blocker-recheck receipt for the same blocker class, root is done. After that, only owner-side blocker conversion work is allowed until the blocker class materially changes.
- No duplicate package rule: before opening a new pass, check whether the exact receipt already exists durably. If it does, do not rerun it unless state changed or scope changed.
- Cluster execution rule: for execution-ready lanes, run execution, then proof or reconciliation, then ratchet as one serial cluster. Do not interleave unrelated root lanes between those steps unless execution becomes blocked.
- One root writer only: at most one root writer, one owner-repo writer, and one optional read-only scout should be active at a time.
- Marker ratchet threshold: a marker moves only when executed state changed, proof-backed adoption widened, manifest-backed restart got broader and stayed refreshed, or one real blocker was cleared. Cleaner wording alone is not enough.
- If one lane blocks and another execution-ready lane remains open, switch lanes and keep the batch moving instead of narrating the same blocker repeatedly.
- Batch routing:
  - owner-side unblock batch -> convert blocker, merge or preserve or archive, recheck blocker class
  - root execution cluster -> blocker recheck if needed, execution, proof or reconciliation, ratchet
  - root read-model or doctrine batch -> only when there is no executable owner-side work ready

Escalation
- Ask before moving or renaming active repos.
- Ask before changing secrets handling, Vercel linkage, or retention policy for backups and installers.
- Ask before deleting runtime residue until its retention class is confirmed.
