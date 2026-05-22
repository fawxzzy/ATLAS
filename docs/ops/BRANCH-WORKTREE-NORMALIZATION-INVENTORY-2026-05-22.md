# Branch & Worktree Normalization Inventory

Date: 2026-05-22
Mode: Inventory and preservation planning only
Status: Active inventory after preservation commit; preserved but not normalized

## Purpose

This lane exists to preserve and classify branch, worktree, stash, and dirty-checkout state before any cleanup, merge, deletion, or broad stack resync work.

Operating rule for this lane:

`Branch name is metadata, not truth. Diff + commits + file ownership are truth.`

## Guardrails

Do not:

- delete branches
- force reset
- run `git clean`
- pop or drop stashes
- blindly commit the large replay branch
- repair or regenerate `stack.lock.yaml` yet
- switch the ATLAS root back to a normalized `main` baseline by force
- move Discord OS code
- start broad cleanup or product implementation work

## Live Facts On 2026-05-22

- The ATLAS root is currently checked out on `main`, not on `replay/steps-cardio-prod-catchup`.
- The ATLAS root `main` is behind `origin/main` by `4` commits and currently has preserved untracked `archive/` residue.
- The local branch `replay/steps-cardio-prod-catchup` still exists and is a real high-risk preservation branch.
- The large replay branch has now been force-committed as a preservation step, but that only changes loss risk. It does not mean the branch is normalized, classified, or ready to merge.
- Across the tracked surfaces there are `142` Git roots including the ATLAS root, `15` repo roots under `repos/`, and `126` Git roots under `tmp/`.
- `32` roots are currently non-clean when the ATLAS root is included.
- Stash state is duplicated across some worktree families, so stash counts must be interpreted per repository family, not per checkout path.

## Branch Discipline After Preservation

The preserve commit changed safety posture, not cleanup posture.

Rules:

- treat `replay/steps-cardio-prod-catchup` as preserved but not normalized
- do not treat a preserved replay branch as automatically mergeable
- no new Codex lane starts until the owner repo and target branch or worktree are explicit
- use clean worktrees for repo-specific lanes
- use ATLAS root branches only for root docs, projection, standards, audits, and coordination work

Pattern:

1. preserve first
2. classify second
3. package third
4. merge or delete only after branch contents are accounted for

Failure Mode:

- a preserved giant branch can still hide generated residue, copied repo content, mixed product slices, and cross-chat inheritance; force-preserving it prevents immediate loss but does not make it clean

## Lockfile Deferral

The current stack lock errors are intentionally deferred in this lane.

Current live blockers:

- `stack.lock.yaml#playbook` pinned commit drift
- `stack.lock.yaml#stack` pinned commit drift

Why they should remain deferred now:

- the ATLAS root is still behind `origin/main`
- preserved recovery residue under `archive/` is still intentional
- branch and worktree classification is not complete
- refreshing the lock now could pin transitional root posture into the governed stack contract

Required sequence:

1. preserve forced replay evidence
2. classify archive, recovery, and package ownership
3. reconcile the root with `origin/main`
4. regenerate `stack.lock.yaml`
5. rerun validation

## Raw Inventory Artifacts

Raw inventory capture files were written under `tmp/scratch/`:

- `tmp/scratch/repo-git-roots-2026-05-22.txt`
- `tmp/scratch/tmp-git-roots-2026-05-22.txt`
- `tmp/scratch/repo-git-meta-2026-05-22.json`
- `tmp/scratch/tmp-git-meta-2026-05-22.json`
- `tmp/scratch/git-root-summary-2026-05-22.json`
- `tmp/scratch/git-common-dir-map-2026-05-22.json`
- `tmp/scratch/repo-branch-inventory-2026-05-22.json`
- `tmp/scratch/atlas-root-meta-2026-05-22.json`
- `tmp/scratch/replay-steps-cardio-branch-analysis-2026-05-22.json`
- `tmp/scratch/replay-steps-cardio-classification-2026-05-22.json`
- `tmp/scratch/atlas-root-untracked-artifacts-2026-05-22.json`

These files are the preservation-first evidence set for any later packaging lane.

`tmp/scratch/replay-steps-cardio-classification-2026-05-22.json` is a local scout artifact. The durable classification summary is recorded in this report and the linked recovery receipts.

Routing output derived from those artifacts:

- `docs/ops/BRANCH-WORKTREE-NORMALIZATION-ROUTING-2026-05-22.md`
- `docs/ops/BRANCH-WORKTREE-ROOT-RECONCILIATION-PREFLIGHT-2026-05-22.md`
- `docs/recovery/ARCHIVE_RETENTION_RECEIPT_2026-05-22.md`
- `docs/recovery/REPLAY_STEPS_CARDIO_PRESERVATION_PACKAGE_2026-05-22.md`
- `docs/recovery/FITNESS_PROGRESSION_PLAYBOOK_SPILLOVER_PACKAGE_2026-05-22.md`

## Repo / Worktree Table

| Surface | Current branch | Upstream state | Dirty state | Stash | Branch pressure | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `.` | `main` | behind `origin/main` by `4` | untracked `archive/` | `4` | `70` local / `40` remote / `31` unique vs local `main` | Root is not safe for normalization yet. |
| `repos/_stack` | `main` | no `origin` / no upstream | clean | `0` | `8` local / `1` remote / `3` unique | `_stack` still has all-local branch history. |
| `repos/ATLAS` | `main` | normal | clean | `0` | `2` local / `24` remote / `1` unique | Small branch drift, not a current dirt hotspot. |
| `repos/fawxzzy-fitness` | `main` | tracks `origin/main` | `13` untracked | `0` | `1` local / `2` remote / `0` unique | Source-of-truth repo is branch-clean but not fully file-clean. |
| `repos/fawxzzy-foundation` | `main` | normal | clean | `0` | `4` local / `4` remote / `0` unique | One local-only Codex branch remains. |
| `repos/fawxzzy-lifeline` | `codex/lifeline-release-replay-verification` | tracks remote Codex branch | `2` untracked | `0` | `26` local / `22` remote / `4` unique | Lifeline has a large parked worktree fleet. |
| `repos/fawxzzy-lifeline-operator-evidence` | `codex/lifeline-operator-evidence` | tracks remote Codex branch | clean | `0` | shared Lifeline branch set | Same repository family as Lifeline. |
| `repos/fawxzzy-mazer` | `main` | normal | clean | `0` | `9` local / `22` remote / `3` unique | Several local-only Codex branches plus Mazer stashes. |
| `repos/fawxzzy-playbook` | `codex/playbook-sustain-docs-audit` | tracks remote Codex branch | `144` untracked / `3` staged | `3` | `39` local / `20` remote / `13` unique / `6` huge | Highest non-ATLAS repo branch pressure. |
| `repos/fawxzzy-playbook-codex` | `main` | normal | clean | `0` | `2` local / `11` remote / `1` unique | Small sidecar branch drift. |
| `repos/fawxzzy-stream` | `main` | no `origin` / no upstream | clean | `0` | `5` local / `0` remote / `4` unique | Local-only repo state requires preservation before sync assumptions. |
| `repos/fawxzzy-trove` | `codex/trove-brand-asset-sync` | tracks remote Codex branch | `3` untracked | `1` | `5` local / `4` remote / `3` unique | Trove also has a preserved local-main stash. |
| `repos/fawxzzy-trove-release-cutover` | `main` | normal | clean | `1` | shared Trove branch set | Same repository family as Trove. |
| `repos/Nat1-Games/nat1-games` | `main` | normal | `1` untracked | `0` | `1` local / `17` remote / `0` unique | Low risk. |
| `repos/playbook-demo/playbook-demo` | `main` | normal | clean | `0` | `1` local / `15` remote / `0` unique | Low risk. |
| `repos/ZachariahRedfield` | `main` | normal | clean | `0` | `1` local / `2` remote / `0` unique | Low risk. |

## Dirty Tmp Worktrees Requiring Preservation

These are the highest-risk non-root checkouts because they already contain staged or high-volume untracked state:

| Path | Branch | Untracked | Staged | Why it is not safe to close |
| --- | --- | ---: | ---: | --- |
| `tmp/fitness-discord-update-bot-clean` | `main` | `1334` | `1295` | Looks like a giant generated or copied-output dump; must be classified before any delete. |
| `tmp/history-ui-archaeology/fawxzzy-fitness` | `main` | `938` | `938` | Large archaeology or replay payload; not safe to discard. |
| `tmp/fitness-discord-main-rollout` | `codex/discord-production-update-bot` | `29` | `16` | Active staged Discord workflow changes. |
| `tmp/playbook-lint-debt-closeout` | `codex/playbook-lint-debt-closeout` | `162` | `0` | Dirty Playbook cleanup branch with shared stashes. |
| `tmp/playbook-main-closeout` | detached `HEAD` | `162` | `0` | Detached Playbook state with identical residue shape. |
| `repos/fawxzzy-playbook` | `codex/playbook-sustain-docs-audit` | `144` | `3` | Active repo root still carrying file drift. |
| `tmp/mazer-o-two-shell` | `codex/mazer-o-two-shell` | `24` | `0` | Dirty Mazer side lane. |
| `tmp/mazer-p-headless-runner` | `codex/mazer-p-headless-runner` | `19` | `0` | Dirty Mazer side lane. |
| `tmp/mazer-ak-v5` | `codex/mazer-ak-v5` | `18` | `0` | Dirty Mazer side lane. |

Secondary dirty worktrees still requiring manifests:

- `repos/fawxzzy-fitness`
- `repos/fawxzzy-lifeline`
- `repos/fawxzzy-trove`
- `tmp/r16-merge`
- `tmp/fawxzzy-stream-2b`
- `tmp/fawxzzy-stream-2c`
- `tmp/release-isolation/fawxzzy-trove-pwa-release`
- `tmp/spotify-club-phase-7`
- `tmp/atlas-foundation-lock-refresh`
- `tmp/atlas-playbook-lock-refresh`
- `tmp/fitness-discord-http-interactions-main-deploy`
- `tmp/fitness-discord-http-interactions`
- `tmp/fitness-discord-http-interactions-forum-tags`
- `tmp/fitness-discord-update-bot-rebased`

## Branch Table

| Repo root | No-upstream branches | Unique branches not on local `main` | Huge-diff branches | Notes |
| --- | ---: | ---: | ---: | --- |
| `.` | `21` | `31` | `2` | Highest branch risk in the stack. |
| `repos/_stack` | `8` | `3` | `0` | `_stack` remains all-local. |
| `repos/fawxzzy-foundation` | `1` | `0` | `0` | Low branch risk. |
| `repos/fawxzzy-lifeline` | `4` | `4` | `0` | Worktree sprawl is the main issue. |
| `repos/fawxzzy-mazer` | `7` | `3` | `0` | Local-only branch preservation needed. |
| `repos/fawxzzy-playbook` | `2` | `13` | `6` | High branch risk and high dirt. |
| `repos/fawxzzy-stream` | `5` | `4` | `0` | No remote branches at all. |
| `repos/fawxzzy-trove` | `1` | `3` | `0` | Moderate branch risk plus stash preservation. |

Exact ATLAS root branches with no upstream and meaningful preservation risk:

- `hotfix/may19-dropdown-runtime-stability`
- `recovery/may19-functional-baseline`
- `replay/current-thread-product-rq-009`
- `replay/current-thread-product-wave-01`
- `replay/discord-connector-prod-catchup`
- `replay/edit-day-dropdown-reorder-parity`
- `replay/older-thread-wave-01`
- `replay/pw-011-progression-layer-spec`
- `replay/pw-012-target-mutation-foundation`
- `replay/pw-013-qualification-window-foundation`
- `replay/pw-014-target-mutation-editor-ui`
- `replay/pw-015-manual-review-checklist-layout`
- `replay/rq-012-edit-day-shared-scaffold`
- `replay/steps-cardio-prod-catchup`

Exact `_stack` local-only branches:

- `codex/stack-auto-land-proof`
- `codex/stack-readme-future-wording-proof`
- `codex/stack-readme-future-wording-proof-main`
- `codex/stack-readme-future-wording-proof-retry`
- `codex/stack-readme-wording-proof`
- `codex/stack-readme-wording-proof-clean`
- `codex/stack-readme-wording-proof-retry`
- `main`

Exact Playbook local-only or unique branches requiring accounting:

- `codex/assistant-reliability-safety-playbook`
- `codex/stabilize-task-ids`
- `codex/assistant-reliability-safety-playbook-clean`
- `codex/codex-inbox-proof-docs-touch-2`
- `codex/fawx-den-os-doctrine`
- `codex/mock-stdin-smoke-nine`
- `codex/mock-watcher-smoke-five`
- `codex/mock-watcher-smoke-six`
- `codex/pattern-discord-verification-gates`
- `codex/playbook-lint-debt-closeout`
- `codex/playbook-sustain-docs-audit`
- `codex/playbook-sustain-pr19-refresh`
- `codex/research-phase-grid-boolean-functions-evidence`
- `codex/research-phase-grid-boolean-functions-math-core`

## Stash Table

| Repo / family | Stash count | Stash entries |
| --- | ---: | --- |
| ATLAS root family | `4` | `codex-post-merge-pr45-closeout-isolation`; `codex-temp-root-lock-refresh`; `r21-pre-clean-regeneration`; `post-r20-normalization-bad-rerun` |
| Playbook family | `3` | `codex-temp-playbook-agents-noise`; `codex-temp-local-hygiene-playbook-docs`; `qa residue before syncing main after PR 8` |
| Trove family | `1` | `codex-preserve-before-sync-2026-05-01` |
| Stream family | `1` | `pre-3c-3d hygiene split` |
| Mazer family | `1` | `split unrelated docs drift from playbook scope lane` |
| Spotify Phase 7 family | `1` | `codex-preserve-generated-artifacts-before-connect-hotfix` |

Interpretation:

- Stashes are active preservation artifacts.
- Shared stashes appear in multiple worktrees because they belong to the same underlying repository family.
- No stash should be popped or dropped until it is exported or intentionally reconciled.

## Huge-Branch Risk Table

| Repo | Branch | Ahead commits | Diff signal | Initial read |
| --- | --- | ---: | --- | --- |
| `.` | `replay/steps-cardio-prod-catchup` | `71` | `4786` files, `759528` insertions, `390` deletions against `origin/main` | Recovery package candidate, not a normal merge branch. |
| `.` | `codex/pr1-stack-lock-refresh` | `3` | `263` files, `379` insertions, `54086` deletions against local `main` | Likely cleanup or regeneration branch; requires preservation review. |
| `repos/fawxzzy-playbook` | `codex/assistant-reliability-safety-playbook-clean` | `20` | `669` files, `15591` insertions, `51602` deletions | Large cleanup branch, not safe for blind closeout. |
| `repos/fawxzzy-playbook` | `codex/stabilize-task-ids` | `2` | `554` files, `713` insertions, `50189` deletions | Large cleanup branch, not safe for blind closeout. |
| `repos/fawxzzy-playbook` | `codex/codex-inbox-proof-docs-touch-2` | `1` | `537` files, `504` insertions, `50160` deletions | Large cleanup branch, likely repo-wide rewrite or prune. |
| `repos/fawxzzy-playbook` | `codex/mock-stdin-smoke-nine` | `1` | `537` files, `496` insertions, `50160` deletions | Same large cleanup profile. |
| `repos/fawxzzy-playbook` | `codex/mock-watcher-smoke-five` | `1` | `537` files, `496` insertions, `50160` deletions | Same large cleanup profile. |
| `repos/fawxzzy-playbook` | `codex/mock-watcher-smoke-six` | `1` | `537` files, `496` insertions, `50160` deletions | Same large cleanup profile. |

## `replay/steps-cardio-prod-catchup` Analysis

Current state:

- The branch exists locally but is not the checked-out branch on 2026-05-22.
- Compared to `origin/main`, it is `71` commits ahead and `4` commits behind.
- Its diff is not a normal app-only delta.

Top-level changed paths:

- `archive`: `4533`
- `docs`: `237`
- `repos`: `13`
- `stack.yaml`: `1`
- `stack.lock.yaml`: `1`
- `README-STACK.md`: `1`

Top file types in the branch diff:

- `.ts`: `1284`
- `.png`: `1006`
- `.tsx`: `847`
- `.json`: `687`
- `.mjs`: `317`
- `.md`: `264`
- `.sql`: `250`

Preserved root archive profile:

- `archive/` currently contains `43900` files and about `2.19 GB`.
- Largest preserved files include `.next` webpack packs, `.git` pack files, and `node_modules` binaries up to `168339758` bytes.

What the branch looks like:

- source code: yes
- docs: yes
- captures/screenshots: yes
- generated build output: yes
- recovery snapshots: yes and dominant
- copied repo content: yes
- duplicate dependency output: likely yes inside archived snapshots
- unknown: low

Recommendation:

- Primary: convert this branch into a recovery package, not a merge candidate.
- Current posture: preserved but not normalized.
- Split preservation into at least three units:
  1. stack docs and notes
  2. captures and proof artifacts
  3. archive snapshot payload plus generated-residue manifest
- After preservation artifacts exist, generated residue can be evaluated for exclusion from future merge paths.
- Manual review is required before any commit, merge, or delete decision.

Classified preservation buckets from the local scout artifact `tmp/scratch/replay-steps-cardio-classification-2026-05-22.json`:

- `archive_snapshot`: `4533` files
- `recovery_docs`: `98` files
- `recovery_captures`: `127` files
- `stack_docs`: `11` files
- `stack_registry_contract`: `4` files
- `repo_touches`: `13` files

Package boundary interpretation:

- `archive_snapshot` is root-owned preserved evidence and should be archived or packaged independently from live root doctrine.
- `recovery_docs` and `recovery_captures` are root-owned recovery dossier material and should stay grouped as a recovery evidence set.
- `stack_docs` are root doctrine and projection surfaces that need separate review from recovery payloads.
- `stack_registry_contract` includes `stack.yaml`, `stack.lock.yaml`, and repo inventory surfaces; these should not be normalized from the replay branch while root lock drift is intentionally deferred.
- `repo_touches` are all a single Fitness progression-playbook slice and should be treated as owner-repo spillover, not as root normalization truth.
- the routing plan now exists, so the next step is preservation manifests and owner handoff inputs, not replay-branch rediscovery
- Preservation Package 1 now exists as the first root-owned receipt, but the replay branch is still preserved rather than normalized
- the Fitness owner-repo spillover now also has its own package note, so both sides of the replay boundary are documented before root reconciliation
- the archive retention receipt now exists, so `archive/**` is retained by named receipt rather than unknown residue
- the root reconciliation preflight still says direct reconcile is not approved until the docs-only normalization state is preserved on `main`

Exact owner-repo spillover currently visible in the replay branch:

- `repos/fawxzzy-fitness/src/components/routines/ProgressionPlaybookEditor.tsx`
- `repos/fawxzzy-fitness/src/lib/progression-playbook-form-state.test.ts`
- `repos/fawxzzy-fitness/src/lib/progression-playbook-form-state.ts`
- `repos/fawxzzy-fitness/src/lib/progression-playbook-ui-options.test.ts`
- `repos/fawxzzy-fitness/src/lib/progression-playbook-ui-options.ts`
- `repos/fawxzzy-fitness/src/lib/progression-playbooks.test.ts`
- `repos/fawxzzy-fitness/src/lib/progression-playbooks.ts`
- `repos/fawxzzy-fitness/src/lib/progression-qualification-window.test.ts`
- `repos/fawxzzy-fitness/src/lib/progression-qualification-window.ts`
- `repos/fawxzzy-fitness/src/lib/progression-status-display.test.ts`
- `repos/fawxzzy-fitness/src/lib/progression-status-display.ts`
- `repos/fawxzzy-fitness/src/lib/progression-target-mutation.test.ts`
- `repos/fawxzzy-fitness/src/lib/progression-target-mutation.ts`

Root reconciliation prerequisites before any `origin/main` reconciliation:

1. Keep the replay branch preserved as evidence, not as the normalization target.
2. Separate archive payload from recovery dossier from root doctrine surfaces.
3. Route the `repo_touches` slice into a Fitness-owner classification decision instead of carrying it as root truth.
4. Keep `stack.lock.yaml` and other stack-registry surfaces deferred until the root is reconciled with `origin/main`.
5. Only after those package boundaries are explicit should root normalization and later lock regeneration proceed.

## Recommended Safe Cleanup Order

1. Freeze this report and the raw `tmp/scratch/` inventory artifacts as the branch/worktree baseline.
2. Treat the forced replay commit as preserved evidence, not as normalized history.
3. Classify what belongs in archive, recovery, package, and stack-doc surfaces.
4. Preserve the root `archive/` payload as its own archive package with size and content manifest.
5. Preserve the dirty Fitness tmp clones with staged or bulk-untracked state, especially `tmp/fitness-discord-update-bot-clean` and `tmp/history-ui-archaeology/fawxzzy-fitness`.
6. Preserve Playbook unique branches and shared stashes before any Playbook cleanup lane.
7. Preserve Lifeline, Stream, Trove, and Mazer local-only branches and stash state.
8. Reconcile the ATLAS root with `origin/main`.
9. Only after root normalization should `stack.lock.yaml` be regenerated and validation re-run against the normalized posture.
10. Only after all meaningful work is packaged should detached clean worktrees be considered close/delete candidates.
11. Only after Branch & Worktree Normalization closes should broad Clean / Re-sync resume.

## Do Not Delete Yet

Exact branch and worktree surfaces that should remain protected:

- `replay/steps-cardio-prod-catchup`
- `replay/discord-connector-prod-catchup`
- `replay/edit-day-dropdown-reorder-parity`
- `replay/current-thread-product-rq-009`
- `replay/current-thread-product-wave-01`
- `replay/older-thread-wave-01`
- `replay/pw-011-progression-layer-spec`
- `replay/pw-012-target-mutation-foundation`
- `replay/pw-013-qualification-window-foundation`
- `replay/pw-014-target-mutation-editor-ui`
- `replay/pw-015-manual-review-checklist-layout`
- `replay/rq-012-edit-day-shared-scaffold`
- `recovery/may19-functional-baseline`
- `hotfix/may19-dropdown-runtime-stability`
- `codex/pr1-stack-lock-refresh`
- `repos/fawxzzy-playbook`
- `tmp/fitness-discord-update-bot-clean`
- `tmp/history-ui-archaeology/fawxzzy-fitness`
- `tmp/fitness-discord-main-rollout`
- `tmp/playbook-lint-debt-closeout`
- `tmp/playbook-main-closeout`
- `tmp/mazer-ak-v5`
- `tmp/mazer-o-two-shell`
- `tmp/mazer-p-headless-runner`
- `tmp/mazer-y-script-typing`
- `tmp/fawxzzy-stream-2b`
- `tmp/fawxzzy-stream-2c`
- `tmp/spotify-club-phase-7`
- every stash listed in the Stash Table

## Safe To Close / Delete Later Candidates

These are candidates for later closure only after preservation packaging is complete:

- `tmp/cortex-surface-reconciliation`
- `tmp/archive-registry-pr45-clean`
- `tmp/atlas-sparse-verify`
- `tmp/pr45-clean`
- `tmp/rollback-check-1716271`
- `tmp/rollback-check-420c5c3`

Reason these are only later candidates:

- they are detached, prunable, or look like clean checkpoint worktrees
- they still share branch or stash context with active repositories
- none should be deleted before the preservation lane confirms their contents are fully accounted for

## Next Codex Package For Preservation / Packaging

```text
At the ATLAS root, continue Branch & Worktree Normalization in preservation mode.

Goal:
Package the risky branch and worktree state without deleting anything.

Do:
- export bundle/patch/manifest artifacts for replay/steps-cardio-prod-catchup
- create an archive manifest for archive/
- create untracked file manifests for dirty tmp worktrees
- create per-repo stash manifests
- create per-repo branch preservation decisions: merge / PR / archive / park
- defer `stack.lock.yaml` regeneration until the ATLAS root is reconciled with `origin/main`

Do not:
- delete branches
- drop stashes
- refresh `stack.lock.yaml` yet
- normalize ATLAS root to clean main by force
- merge the replay branch blindly
- resume broad clean/resync yet
```

## Marker Table

Percentages below use the consolidated marker model going forward.

- Verta Absorption: `99%`
- Archive Normalization: `100%`
- ATLAS Core Phase: `92%`
- `_stack` Readiness: `40%`
- Foundation Alignment: `100%`
- Lifeline Readiness: `97%`
- Playbook Maturity: `92%`
- Cortex Readiness: `35%`
- Fitness Source-of-Truth Reset: `100%`
- Fitness QA/LLEL Workflow: `96%`
- Fitness Branch Cleanup / Main-Only Governance: `96%`
- Fitness Recovery Preservation: `80%`
- Branch & Worktree Normalization: `50%`
- Unified Workflow Convergence: `0%`
- Inventory & Truth Map: `15%`
- Full Stack Re-sync, Clean & Closeout: `22% paused`
- Vision & Future Alignment: `0%`
- Dependency Untangling: `0%`
- Playbook Everywhere + Cortex Interface: `0%`
- Knowledge Capture & Transfer: `10%`
- Feedback Loop Readiness: `0%`
- Sandbox Simulation Readiness: `0%`
- AI Long-Run Batch Orchestration: `20%`
- Truth Map & ATLAS Book: `0%`
- Discord OS Extraction Review: `0%`
- Discord Workflow & Documentation Publishing: `0%`
- Post-Convergence Lane Split Readiness: `0%`
