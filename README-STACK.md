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

Read these files first:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `AGENTS.md`
- `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`
- `docs/architecture/STACK-STANDARDS.md`
- `docs/architecture/PATH-POLICY.md`
- `docs/ops/ATLAS-SESSION-RUNBOOK.md`
- `docs/ops/ATLAS-CODEX-CONTEXT-RUNBOOK.md`
- `docs/ops/ATLAS-TOOL-REGISTRY-RUNBOOK.md`
- `docs/ops/ATLAS-STATUS-RUNBOOK.md`

## Current Posture

ATLAS root and Cortex now form an awareness and coordination core built on explicit files and read models rather than repo folklore.

- major awareness primitives are present
- governed sessions and governed resume are real
- the first bounded truthful write exists
- the next compounding layer is initiative management above sessions, not basic awareness discovery

Current operating call:

- grounded text conversation is ready for bounded daily operator use
- voice companion is still a beta candidate pending one clean live certification pass
- the blocking proof is operational trust, not missing backend architecture
- the next build after that pass should be a thin cockpit over the Awareness API, not more backend plumbing

For ATLAS platform architecture doctrine, use `repos/fawxzzy-atlas/README.md` and the docs under `repos/fawxzzy-atlas/docs/` as the canonical source. Stack-root docs should stay stack- and boundary-oriented and should link back to Atlas instead of duplicating platform specs.

## Canonical Repo Ids

Use these ids in stack docs, tickets, and automation:

- `stack` -> `.`
- `_stack` -> `repos/_stack`
- `atlas` -> `repos/fawxzzy-atlas`
- `playbook` -> `repos/fawxzzy-playbook`
- `lifeline` -> `repos/fawxzzy-lifeline`
- `fitness` -> `repos/fawxzzy-fitness`
- `mazer` -> `repos/fawxzzy-mazer`
- `stream` -> `repos/fawxzzy-stream`
- `nat1-games` -> `repos/Nat1-Games/nat1-games`

The ids are canonical even where disk names have not been normalized yet.

`repos/**` remains untracked by the root repo as a code surface. The stack root tracks inventory and policy about those repos, not mirrored copies of their source trees.

## Root-Owned Subsystems

- `cortex` -> `runtime/cortex`

`repos/cortex` is adjacent historical context only. The active Cortex runtime surface is root-owned under `runtime/cortex/**`.

## Root Artifact Lanes

- sessions -> `runtime/atlas/sessions`
- context packs -> `runtime/atlas/context-packs`
- descriptor registry -> `runtime/cortex/artifacts`
- worker execution receipts -> `runtime/lifeline/worker-execution`
- governed tool and extension registries -> `docs/registry`

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
- execution / capability / approvals / tools -> Lifeline
- orchestration / worker flow / resume / merge -> `_stack`
- doctrine / UAPI / platform contracts -> Atlas repo
- knowledge / evidence / promotion / query -> knowledge lane
- topology / git / repo visibility -> repo inventory + lock + debt ledger
- operator / chat / session / initiative -> awareness + status + working memory

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
