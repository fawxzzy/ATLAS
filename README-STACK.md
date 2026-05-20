# ATLAS Stack

ATLAS is a portable stack root. It is the filesystem contract above the repos, not another application repo.

This root exists to make the stack rebuildable, zip-safe, and path-independent:

- source lives in `repos/`
- retained runtime state lives in `runtime/`
- durable non-secret imports and fixtures live in `data/`
- bundles, patches, and releases live in `packages/`
- stack docs and standards live in `docs/`
- shared scripts live in `ops/`
- disposable artifacts live in `tmp/`
- secrets live only in `secrets/`

## Control Repo Boundary

ATLAS root is the control repo and coordination layer. It is not a second umbrella source repo.

- child repos under `repos/**` stay independent git roots
- root-owned visibility for those repos is published through inventory and audits, not by vendoring repo content into root
- repo-local commands should run against the child repo path directly, for example `pnpm -C repos/fawxzzy-playbook ...`
- committed topology visibility lives in `docs/registry/STACK-REPO-INVENTORY.json` and `docs/audits/STACK-REPO-INVENTORY.md`

Root rule:

- federate repo truth
- do not duplicate repo truth
- freeze importable platform contracts at root before owner-repo auth or runtime package work

Read these files first:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/registry/STACK-SYNERGY-REGISTRY.json`
- `AGENTS.md`
- `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
- `docs/architecture/STACK-STANDARDS.md`
- `docs/architecture/atlas-platform-v1.md`
- `docs/architecture/repo-class-admission-rules.md`
- `docs/architecture/PATH-POLICY.md`
- `docs/ops/ATLAS-MISSION-CONTEXT.md`
- `docs/ops/ATLAS-SESSION-RUNBOOK.md`
- `docs/ops/ATLAS-CODEX-CONTEXT-RUNBOOK.md`
- `docs/ops/ATLAS-TOOL-REGISTRY-RUNBOOK.md`
- `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
- `docs/ops/ATLAS-STATUS-RUNBOOK.md`
- `docs/ops/ATLAS-COCKPIT-RUNBOOK.md`
- `docs/ops/ATLAS-LIFELINE-PLATFORM-RESTART.md`
- `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
- `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`
- `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
- `docs/codex/FAST-ITERATION-LOOP.md`

## Current Posture

ATLAS is now an awareness-first, federated operator platform built on explicit files and read models rather than repo folklore.

- the cockpit is landed as a thin read-only operator surface
- Playbook convergence and continuity lanes are landed
- reviewed Verta derivative notes are landed without changing Verta trust posture
- root remains the selector and report surface, not a second truth store

Current operating call:

- grounded text conversation is ready for bounded daily operator use
- `fitness` is the first bounded `verified` repo at `verification_scope=targeted`
- `mazer` is now the second bounded `verified` repo at `verification_scope=targeted`
- stack-wide source-verified synergy discovery is landed enough at root for tranche selection
- Wave 1 contract freeze, adoption, instrumentation, reusable workflow lane, and warehouse smoke-check lane are landed in the scope actually frozen
- Atlas and Fitness caller workflows are pinned to immutable Playbook ref `9ce397e893e4007afbe93366770867ed64f66500`
- the first projection artifact for that lane lives at `docs/registry/STACK-SYNERGY-REGISTRY.json` and records landed owner lanes plus the projected Fitness Wave 2 metrics, funnel, and growth posture without changing owner-repo truth
- first-wave owner surfaces still include Lifeline execution, capability, approval, proof-pass receipt, and worker-execution receipt semantics; Playbook governance, verify, reusable workflow, and warehouse-pack reuse; and `_stack` orchestration, merge, resume, and worker contracts
- keep `status`, `merge_request`, `conversation`, `session`, `proposal`, `day_summary_taxonomy`, `heartbeat`, `execution_rejected`, and `execution_expired` as candidate rows until repo evidence promotes them
- Fitness owner truth now includes the first growth pack, the pilot-readiness threshold pack, and measured proof for one shadow-only placement in the Wave 2 growth lane
- the pilot-readiness gate currently evaluates to `stay_shadow` in Fitness owner truth, so no pilot-live rollout is authorized at root
- the next owner-repo work is evidence-surface completion in `repos/fawxzzy-fitness` so the frozen pilot thresholds can be measured from repo-owned receipts
- Fitness Discord community truth now includes live feedback export/sync, update-post curation, emoji bootstrap, Fawx Security reversible moderation, and server inventory/noise-audit tooling
- the canonical feedback workflow is now locked as:
  - Feedback forum card
  - thread-visible audit comments for card mutations
  - board export artifacts
  - reviewed Verta Core / Playbook planning input
  - curated Update Bot promotion only for user-facing releases
- Discord remains the visible community/update/support surface; ATLAS receives durable reviewed summaries rather than raw card-by-card task duplication
- Fawx Security moderation is now proven live on non-owner users:
  - warnings and severity are live
  - Purgatory is reversible role isolation
  - `Verified` is removed during jail and restored on release
  - non-access roles such as `Fawxzzies` stay preserved
  - no-ban default is enforced
- Fitness Discord ops now inventory channels, roles, emojis, and forum tags directly from the live guild
- the Discord noise policy is now explicit:
  - only `Updates` and `Main` are loud channels
  - feedback and moderation workflows avoid broad pings
  - the bot does not claim it can force user-level personal mute settings
- auth, shared UI, cross-sell, and ML stay explicitly later
- voice remains intentionally below the line unless explicitly chosen
- the decision gate stays explicit: root sessions change projection truth; owner-repo sessions change owner truth

Roadmap addition:

- cross-repo Playbook convergence and durable conversation continuity are now tracked as an explicit stack program in `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md`
- that program complements the operator cockpit slice; it does not convert the root into an umbrella monorepo or replace repo-owned doctrine
- the platform-cutover restart posture is tracked in `docs/ops/ATLAS-LIFELINE-PLATFORM-RESTART.md`
- that restart keeps ATLAS root as coordinator, `lifeline` as execution owner, and `playbook` as codification owner; it does not move platform implementation truth into a separate umbrella repo
- root execution docs should link to Lifeline's canonical contract set instead of restating those semantics locally:
  - `repos/fawxzzy-lifeline/docs/contracts/privileged-execution-contract.md`
  - `repos/fawxzzy-lifeline/docs/contracts/ui-proof-passed-receipt-contract.md`
  - `repos/fawxzzy-lifeline/docs/ops/lifeline-operator-surface.md`
  - `repos/fawxzzy-lifeline/docs/runbooks/hermetic-validation-operator-flow.md`
- the rapid localhost iteration workflow is now tracked in `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
- its default posture is two-speed validation: affected-screen checks every iteration, broader screenshot sweeps only at checkpoints
- named session bootstraps are now tracked through `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
- the first named mode binds natural-language openers to canonical workflow and prompt docs so Codex can recognize `fast-iteration-loop` as an Atlas contract instead of free-form instruction

For ATLAS platform architecture doctrine in this workspace, use the stack-root architecture docs under `docs/architecture/` as the canonical source. A dedicated `repos/fawxzzy-atlas` checkout is not present in this stack view.

## Canonical Repo Ids

Use these ids in stack docs, tickets, and automation:

- `stack` -> `.`
- `_stack` -> `repos/_stack`
- `playbook` -> `repos/fawxzzy-playbook`
- `lifeline` -> `repos/fawxzzy-lifeline`
- `foundation` -> `repos/fawxzzy-foundation`
- `fitness` -> `repos/fawxzzy-fitness`
- `mazer` -> `repos/fawxzzy-mazer`
- `trove` -> `repos/fawxzzy-trove`
- `stream` -> `repos/fawxzzy-stream`
- `nat1-games` -> `repos/Nat1-Games/nat1-games`

The ids are canonical. Fitness is normalized on disk at `repos/fawxzzy-fitness`; other repo disk names may still differ where explicitly noted.

`repos/**` remains untracked by the root repo as a code surface. The stack root tracks inventory and policy about those repos, not mirrored copies of their source trees.

## Deferred Adjacent Surfaces

Some local repo roots may exist under `repos/` without being admitted stack members.

- current deferred adjacent examples include `repos/ATLAS`, `repos/fawxzzy-playbook-codex`, `repos/fawxzzy-fitness-parity-recovery`, `repos/fawxzzy-fitness-recovered`, `repos/fawxzzy-fitness.reclone.20260502-195639`, and `repos/ZachariahRedfield`
- these surfaces are not canonical repo ids
- they stay excluded from governed topology until an explicit admission decision updates `stack.yaml`, `stack.lock.yaml`, the published inventory, and owner-usage notes together
- Verta-Core remains a separate quarantined trust-gate surface, not an adjacent managed repo

## Root-Owned Subsystems

- `cortex` -> `runtime/cortex`

`repos/cortex` is adjacent historical context only. The active Cortex runtime surface is root-owned under `runtime/cortex/**`.

## Root Artifact Lanes

- sessions -> `runtime/atlas/sessions`
- context packs -> `runtime/atlas/context-packs`
- descriptor registry -> `runtime/cortex/artifacts`
- worker execution receipts -> `runtime/lifeline/worker-execution`
- governed tool and extension registries -> `docs/registry`

The worker-execution receipt lane is a root-visible runtime lane for Lifeline-owned receipts. The root may index and route those artifacts, but Lifeline remains the canonical owner of receipt semantics.

## Codex Context

Root-launched Codex work should use intent-routed context packs instead of broad stack dumps.

- builder -> `ops/atlas/build_codex_context.py`
- prompt renderer -> `ops/atlas/prepare_codex_task.py`
- output lane -> `runtime/atlas/context-packs/<task-id>/`

Bootstrap order for root Codex work:

1. `stack.yaml`
2. `stack.lock.yaml`
3. `docs/registry/STACK-REPO-INVENTORY.json`
4. relevant awareness slices
5. related initiative, proposal, and trust refs
6. only then target repo docs or code

Intent routing:

- governance / policy / verification -> Playbook
- execution / capability / approvals / proof-pass receipts / tools -> Lifeline
- orchestration / worker flow / resume / merge -> `_stack`
- doctrine / UAPI / platform contracts -> Atlas repo
- knowledge / evidence / promotion / query -> knowledge lane
- topology / git / repo visibility -> repo inventory + lock + debt ledger
- operator / chat / session / initiative -> awareness + status + working memory

Execution contract refs:

- canonical execution lineage -> `repos/fawxzzy-lifeline/docs/contracts/privileged-execution-contract.md`
- canonical proof-pass receipt semantics -> `repos/fawxzzy-lifeline/docs/contracts/ui-proof-passed-receipt-contract.md`
- canonical operator flow -> `repos/fawxzzy-lifeline/docs/ops/lifeline-operator-surface.md`
- canonical hermetic validation flow -> `repos/fawxzzy-lifeline/docs/runbooks/hermetic-validation-operator-flow.md`

## Branding

ATLAS now owns the canonical sigil at the stack root.

- source of truth -> `branding/source/`
- generated derivatives -> `branding/generated/`
- consumer mapping -> `branding/manifest.json`
- workflow + policy -> `docs/standards/BRANDING-ASSET-PIPELINE.md`

Consumer repos should receive generated or synced copies only. Do not hand-manage brand assets per repo.

## Working Rules

1. Start at `C:\ATLAS` only for stack-wide work, audits, standards, packaging, or cross-repo routing.
2. Do single-repo implementation work inside the target repo, not from the stack root.
3. Do not commit machine-specific absolute paths in stack docs or config.
4. Do not store logs, screenshots, or runtime state in repo roots when a stack bucket exists.
5. Do not let default exports include `secrets/`, `.env*`, `runtime/`, or `tmp/`.
6. Keep live implementation truth in the owning repo; ATLAS docs should stay lineage- and boundary-oriented.
7. For recovered machine material, catalog first and delete originals only after verified-safe classification.

## Packaging and Exports

Use explicit destinations:

- patches -> `packages/patches`
- bundles -> `packages/bundles`
- prebuilt outputs -> `packages/prebuilt`
- releases -> `packages/releases`
- source snapshots -> `packages/snapshots`

Never put release bundles or snapshots directly in `repos/`.

## Runtime and Temp Output

Use these roots instead of repo roots:

- long-lived non-secret state -> `runtime/`
- disposable logs and captures -> `tmp/`

Examples:

- dev server logs -> `tmp/logs`
- browser screenshots -> `tmp/captures`
- preview outputs -> `tmp/previews`
- Codex runner state -> `runtime/codex`

## Secrets

`secrets/` is the only stack-level secret bucket.

- `secrets/templates/` may contain redacted examples
- `secrets/local/` is for machine-local material only

Do not place secrets in docs, packages, runtime exports, or default snapshots.
