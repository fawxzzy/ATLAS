# ATLAS Structure Audit

Audit date: 2026-04-08

Scope:

- Read-only audit of the ATLAS root
- No application code changes
- Secret contents not inspected
- Focus on portability, rebuildability, path independence, and stack truth
- Broad binary/build trees excluded from detailed path scans unless they affected structure classification

## Executive summary

The ATLAS root has the right high-level shell, but the current structure truth is split across a stale root manifest, path-coupled `_stack` docs, and Atlas architecture docs that still describe a `dev/` dispatcher layer that does not exist at the ATLAS root. At the same time, the root support directories meant to hold shared state are empty, while runtime and generated state still live inside active repos.

The biggest structural problem is namespace mixing under `repos\`: active source repos, nested wrapper repos, legacy source repos, Unreal build caches, installers, videos, zip drops, and backup bundles all sit side by side. That makes the stack hard to reason about, hard to rebuild on another machine, and easy to break with path-sensitive changes.

## Evidence-backed findings

### 1. Root stack truth is stale and path-coupled

- `stack.yaml` hardcodes absolute paths instead of stack-relative references.
- `stack.yaml` lists only two repos under `repos:`.
- One listed repo path is broken: `playbook: repos/playbook` does not exist.
- The manifest omits active repos such as `_stack`, `fawxzzy-atlas`, `fawxzzy-fitness`, `fawxzzy-lifeline`, `fawxzzy-mazer`, and `fawxzzy-playbook`.

Impact:

- Any bootstrap or automation that trusts `stack.yaml` is already operating on incomplete truth.

### 2. `_stack` still documents the old workspace root

Observed in:

- `repos/_stack/README.md`
- `repos/_stack/AGENTS.md`

Examples:

- `Start in the prior workspace root`
- `prior-workspace-root/_stack`
- `prior-workspace-root/fawxzzy-mazer`
- `prior-workspace-root/AGENTS.md`

Impact:

- `_stack` is the operator layer, so stale path truth here propagates directly into workflow usage and future automation.

### 3. Atlas docs describe a dispatcher layer that is not present at the ATLAS root

Observed in:

- `repos/fawxzzy-atlas/README.md`
- `repos/fawxzzy-atlas/docs/STACK_OVERVIEW.md`
- `repos/fawxzzy-atlas/docs/SYSTEM_REGISTRY.md`
- `repos/fawxzzy-atlas/docs/LOCAL_FIRST_WORKFLOW.md`

Evidence:

- The docs repeatedly describe `dev/` as the dispatcher layer.
- No `dev/` directory exists at the ATLAS root.

Impact:

- Architecture truth does not currently match filesystem truth.

### 4. Root support directories are empty while shared concerns live inside repos

Observed:

- `runtime/`, `data/`, `packages/`, `ops/`, and `tmp/` are empty.
- Shared/runtime/generated state is instead scattered under repos:
  - `_stack\queue`, `_stack\receipts`, `_stack\ops`
  - repo-local `.playbook\`
  - repo-local `.lifeline\`
  - repo-local `.codex\`
  - committed screenshots/logs in `fawxzzy-mazer`
  - parent-level `.playbook\` state in `Nat1-Games`

Impact:

- ATLAS does not yet have a reliable separation between source, operations, runtime state, and generated artifacts.

### 5. `repos\` mixes active repos with wrappers, legacy content, backups, installers, and media

Observed entries:

- Active source repos: `_stack`, `cortex`, `fawxzzy-atlas`, `fawxzzy-fitness`, `fawxzzy-lifeline`, `fawxzzy-mazer`, `fawxzzy-playbook`
- Nested/wrapper roots: `Nat1-Games`, `playbook-demo`, `playbook-old`, `mazer-legacy-unreal`
- Binary/media drops: `Hard Pill To Swallow`, `Realm Blade`
- Backup artifacts: `repo-backups`
- Zip drops at `repos\` root

Impact:

- Canonical repo discovery is ambiguous.
- Structural edits become riskier because “repo” no longer means “source root.”

### 6. Several entries under `repos\` are not canonical roots

Observed actual roots:

- `repos/Nat1-Games/nat1-games`
- `repos/playbook-demo/playbook-demo`
- `repos/playbook-old/playbookv1`
- `repos/mazer-legacy-unreal/Mazer`

Impact:

- Relative path conventions and workspace-wide automation cannot safely assume `repos\<name>` is the runnable repo root.

### 7. Repo hygiene contracts are inconsistent

Observed mismatches:

- `_stack` has `.codex\` but no `.codex\config.toml`
- `fawxzzy-fitness` has `.codex\` but no `.codex\config.toml`
- `fawxzzy-lifeline` has `.codex\` but no `.codex\config.toml`
- `fawxzzy-atlas` has `README.md` but no `AGENTS.md`
- `fawxzzy-fitness` uses `AGENT.md` instead of `AGENTS.md`
- `Nat1-Games\nat1-games` has `AGENTS` without `.md`
- Several wrapper/archive entries have no README or agent contract at their visible root

Impact:

- Operator expectations vary by repo.
- Codex automation cannot rely on a single contract shape.

### 8. Validation tooling is uneven across the repo set

Strongly defined:

- `cortex`
- `fawxzzy-fitness`
- `fawxzzy-lifeline`
- `fawxzzy-mazer`
- `fawxzzy-playbook`

Weak or unclear at visible root:

- `fawxzzy-atlas`
- wrappers and archive-style entries
- binary/media drops

Impact:

- Structural changes cannot yet be safely sequenced across the whole stack using one validation matrix.

### 9. Generated and review artifacts are committed into active source roots

Examples:

- `repos/fawxzzy-mazer/dist`
- numerous `artifacts-*.png`, `review-*.png`, and `.tmp-*.log` files in `fawxzzy-mazer`
- `repos/Nat1-Games/.playbook/...`
- `repos/mazer-legacy-unreal/Mazer/Binaries`, `DerivedDataCache`, `Intermediate`, `Saved`

Impact:

- Source and generated state are not cleanly separated.
- Portability and rebuildability degrade because machine-local outputs are part of the visible structure.

### 10. There is active hygiene drift even inside core repos

Observed:

- `repos/fawxzzy-playbook/README.md` contains unresolved merge conflict markers.

Impact:

- Even before structural edits, some active stack truth is not in a clean, publishable state.

## Repo inventory

| Repo/root | Purpose inference | Confidence | Structural note |
| --- | --- | --- | --- |
| `repos\_stack` | Shared operator/workflow repo | High | Main source of path-coupled docs; should align with root `ops\`. |
| `repos\cortex` | Python framework snapshot | High | Not represented in Atlas stack docs; currently outside the named core stack. |
| `repos\fawxzzy-atlas` | Architecture/contracts/planning repo | High | Docs-first; missing repo-local agent contract. |
| `repos\fawxzzy-fitness` | Fitness app | High | Has singular `AGENT.md` and repo-local runtime state. |
| `repos\fawxzzy-lifeline` | Local runtime/operator CLI | High | Strong validation surface; missing agent contract/config consistency. |
| `repos\fawxzzy-mazer` | Mazer rebuild app | High | Active source mixed with screenshots and logs. |
| `repos\fawxzzy-playbook` | Playbook monorepo | High | Strong contract surface; README conflict needs cleanup. |
| `repos\Hard Pill To Swallow` | Installer/media drop | Medium | Not a canonical source repo. |
| `repos\mazer-legacy-unreal\Mazer` | Legacy Unreal source project | High | Canonical root is nested and includes heavy generated directories. |
| `repos\Nat1-Games\nat1-games` | Nested app repo | Medium | Parent contains generated Playbook state outside actual repo root. |
| `repos\playbook-demo\playbook-demo` | Demo fixture repo | High | Nested canonical root. |
| `repos\playbook-old\playbookv1` | Legacy Playbook v1 repo | High | Nested canonical root. |
| `repos\Realm Blade` | Installer/media drop | Medium | Not a canonical source repo. |
| `repos\repo-backups` | Backup bundle/patch drop | High | Archive area, not source. |

## Mixed concerns detected outside canonical boundaries

- Workspace operator assets live under active repo `_stack` while root `ops\` is empty.
- Generated Playbook state exists both inside active repos and in wrapper parents.
- Archive artifacts live beside active repos.
- Build screenshots/logs are committed into active app roots instead of a dedicated snapshots/runtime location.

## Top 10 structural issues

1. `stack.yaml` is stale, absolute-path-based, and incomplete.
2. `_stack` docs and rules are still coupled to the prior workspace root.
3. Atlas architecture docs still depend on a nonexistent `dev/` layer.
4. Root support directories are empty while shared concerns remain embedded inside repos.
5. `repos\` mixes active source, demos, legacy, binaries, and backups.
6. Several visible entries under `repos\` are wrappers rather than canonical roots.
7. AGENTS/README/.codex contracts are inconsistent across active repos.
8. Validation coverage is uneven or unclear at the visible repo root level.
9. Generated artifacts and runtime state are mixed into source roots.
10. Active core docs already contain unresolved hygiene drift (`fawxzzy-playbook\README.md`).

## Top 10 fixes in execution order

1. Normalize `stack.yaml` into the canonical relative-path registry.
2. Freeze and document canonical repo roots and role categories.
3. Remove old machine-specific paths from `_stack` docs and agent rules.
4. Reconcile Atlas architecture docs with the real root layout.
5. Standardize the minimum repo contract for active repos.
6. Fill the contract gaps in active repos before any moves.
7. Define and enforce runtime/generated-state placement rules.
8. Untangle wrapper folders from canonical roots.
9. Rehome legacy, demo, backup, installer, and media entries out of the active repo namespace.
10. Clean residual hygiene drift in active repos after the structural contracts are stable.

## Risky moves that should wait

- Renaming active repo directories.
- Moving `_stack` before its runner contracts are rewritten.
- Flattening nested repos before their canonical roots are formally adopted.
- Deleting legacy Unreal generated directories without a retention decision.
- Purging repo-local runtime state before its new home is defined.
- Moving binary drops and backup bundles before provenance/checksum expectations are documented.
- Any change to `secrets\` beyond documenting its contract.

## Unknowns

- Whether `cortex` is intended to be a first-class ATLAS stack component or an adjacent research/vendor repo.
- Whether `Nat1-Games` parent-level `.playbook\` state should be preserved, relocated, or discarded.
- Whether binary-only entries (`Hard Pill To Swallow`, `Realm Blade`) need long-term retention inside ATLAS.
- Whether wrapper folder names are deliberate compatibility shims or just accumulation.

## Recommended next step

Do a docs-and-manifest-only normalization pass first:

- fix stack truth
- standardize active repo contracts
- classify every `repos\` entry
- define where runtime/generated/archive content belongs

Only after that should physical moves or rename operations start.
