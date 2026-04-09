# ATLAS Root Rules

Scope
- Applies to sessions launched from `C:\ATLAS`.
- This file governs stack-wide work at the ATLAS root.
- Repo-local `AGENTS.md` files override this file inside their own repo roots.

Purpose
- The ATLAS root is the stack coordination layer.
- Use it for standards, architecture, path policy, packaging rules, audits, and cross-repo planning.
- Do not treat the ATLAS root as a normal application repo.

Routing
- Single-repo implementation work should be routed into the target repo root.
- Cross-repo work may touch only the named repos plus stack-level files under `C:\ATLAS`.
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
- Keep committed paths relative to `C:\ATLAS` whenever possible.
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

Parallelism
- Use one agent per repo or one non-overlapping stack file slice.
- Do not let multiple agents edit the same repo root without a clear ownership split.

Escalation
- Ask before moving or renaming active repos.
- Ask before changing secrets handling, Vercel linkage, or retention policy for backups and installers.
- Ask before deleting runtime residue until its retention class is confirmed.
