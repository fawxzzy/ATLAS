# GitHub Control-Plane Opening Audit — 2026-07-12

Status: corrected read-only opening evidence; no GitHub, owner-repository, worktree, branch, Vercel, Supabase, Discord, marker, or percentage mutation is authorized by this audit.

## Evidence Method

Fresh evidence was collected from 2026-07-12T10:45:12.355703Z through 2026-07-12T10:58:57.680276Z UTC. The authenticated GitHub CLI account was `fawxzzy` (User), using the canonical local CLI installation read-only. The CLI executable's machine-specific absolute path is deliberately omitted from the committed contract. No token, credential, or secret value was retrieved, retained, printed, or copied.

Evidence surfaces: `stack.yaml`; `stack.lock.yaml`; `docs/registry/STACK-REPO-INVENTORY.json`; local `git rev-parse`, `git branch --show-current`, `git remote get-url`, `git status --porcelain`, `git rev-list --left-right --count`, and `git worktree list --porcelain`; authenticated GitHub REST repository/branch/compare/PR/issue/Actions/release/classic-protection/ruleset/Dependabot/secret-scanning endpoints; and read-only `gh run view` job/step plus filtered failure-log signals. Local tracking parity was measured without fetch and is kept separate from live cloud-default comparison.

Endpoint semantics are preserved. HTTP 404 from classic branch protection means `not_enabled_or_not_found`, not a protected or denied inference. If classic protection and rulesets disagree, aggregate truth is `conflicting`; if either is access-denied or unresolved, aggregate truth is `unknown`. Dependabot HTTP 403 is `access_denied` with count `unknown`, never zero. Bounded Actions samples and empty release results are not global health claims.

The failed-run bundle under `tmp/failed-runs/github-control-plane-opening-audit-20260712T100856870Z` was consulted only as a candidate inventory. Every promoted volatile fact was recollected from current local Git or live GitHub.

## Executive Finding

The ten-repository `fawxzzy` cloud inventory is reachable and deterministic, but the opening gate is not a health closeout. Nine default branches lack both visible classic protection and visible repository rulesets; Lifeline alone has classic `main` protection. No releases are visible. Dependabot alert counts are unknown for all ten repositories because every alert endpoint returned HTTP 403. Playbook and Fitness have exact owner-side CI recovery queues. Fitness also has one open Critical secret-scanning alert and remains separately resume-blocked.

## Registry-to-GitHub Reconciliation

| Repository | stack.yaml | stack.lock.yaml | Published inventory | Current reconciliation |
| --- | --- | --- | --- | --- |
| ATLAS | governed | not_locked | stale | stale projection recorded; not repaired |
| DiscordOS | governed | current | current | current |
| _stack | governed | stale | stale | stale projection recorded; not repaired |
| cortex | remote_only_subsystem_boundary | not_locked | not_applicable_remote_only | remote-only boundary |
| fawxzzy-fitness | governed | not_locked | current | current |
| foundation | governed | current | current | current |
| lifeline | governed | current | current | current |
| mazer | governed | not_locked | current | current |
| playbook | governed | current | current | current |
| trove | governed | current | current | current |

`stack.yaml` declares Stream as a local incubating repository with no origin and Cortex as a root-owned subsystem at `runtime/cortex` with unresolved remote provenance. `stack.lock.yaml` covers nine components but intentionally does not lock ATLAS, Fitness, Mazer, or remote-only Cortex. The current published inventory has 12 repository rows; Playbook Demo and Nat1 Games remain governed but outside this exact `fawxzzy` ten-repository scope. ATLAS and `_stack` published heads are stale relative to current local Git, and `_stack`'s lock pin is also stale; this audit records those facts without mutating projections.

## Per-Repository Local and Cloud Facts

| Repository | Local path | Branch / HEAD | Tracking parity | Live cloud-default comparison | Dirt | Worktrees | Cloud default / HEAD | Branches |
| --- | --- | --- | --- | --- | ---: | ---: | --- | ---: |
| ATLAS | `.` | `main` / `c31ff1070a3ee3f2864f23484d34aded2859fb39` | equal (ahead 0, behind 0) | identical (cloud ahead 0, cloud behind 0) | 17 | 4 | `main` / `c31ff1070a3ee3f2864f23484d34aded2859fb39` | 52 |
| DiscordOS | `repos/DiscordOS` | `codex/mazer-viewport-board-status` / `b173de1549f85cbde040aa6a7ddeba959c7dc524` | equal (ahead 0, behind 0) | diverged (cloud ahead 12, cloud behind 2) | 0 | 12 | `main` / `5a87166b001766ba40ba1d152824398f13788443` | 11 |
| _stack | `repos/_stack` | `main` / `5ea6b712b91a691689b619addb8f8ba649126661` | equal (ahead 0, behind 0) | identical (cloud ahead 0, cloud behind 0) | 0 | 40 | `main` / `5ea6b712b91a691689b619addb8f8ba649126661` | 5 |
| cortex | `null` | null / null | not_applicable | not_applicable | null | 0 | `main` / `495808fde487b3bdca2de283ff53f748b0b84630` | 1 |
| fawxzzy-fitness | `repos/fawxzzy-fitness` | `main` / `e1ab7fbea979456380230c5459fdef6ae4c927e9` | equal (ahead 0, behind 0) | identical (cloud ahead 0, cloud behind 0) | 34 | 2 | `main` / `e1ab7fbea979456380230c5459fdef6ae4c927e9` | 6 |
| foundation | `repos/foundation` | `main` / `5cedd6234755be3d637abc33572b905dce3b8f7c` | equal (ahead 0, behind 0) | identical (cloud ahead 0, cloud behind 0) | 0 | 1 | `main` / `5cedd6234755be3d637abc33572b905dce3b8f7c` | 4 |
| lifeline | `repos/lifeline` | `codex/path-discipline-warning-slice-lifeline` / `538f623a84b003e70dadd234e6ea3af642446a5f` | equal (ahead 0, behind 0) | local_ahead_of_cloud (cloud ahead 0, cloud behind 2) | 0 | 1 | `main` / `31ef3ad92c775810b19cc565820664f3476a6719` | 23 |
| mazer | `repos/mazer` | `codex/player-goal-default-colors` / `a537d2d17429bdf0482989c280373a6ea751f9c0` | equal (ahead 0, behind 0) | local_behind_cloud (cloud ahead 10, cloud behind 0) | 1 | 9 | `main` / `8ced175c65cfb36bb057cf25e93f59819c57803b` | 28 |
| playbook | `repos/playbook` | `codex/path-discipline-warning-slice-playbook` / `10b8f0ac044a7f9c66b4aa8dd08f6abd2d1c5269` | equal (ahead 0, behind 0) | diverged (cloud ahead 7, cloud behind 13) | 0 | 1 | `main` / `aab5ad5b4a51f37f6426b0797080dfa565954788` | 20 |
| trove | `repos/trove` | `codex/path-discipline-warning-slice-trove` / `437c7604adee02e0403d77f75162a6c5f232221f` | equal (ahead 0, behind 0) | local_ahead_of_cloud (cloud ahead 0, cloud behind 4) | 0 | 1 | `main` / `ed51c69643047e1c59bb1caa310900ac6d526d8a` | 5 |

Remote-only Cortex has local path `null`; the embedded `runtime/cortex` subsystem is not treated as its checkout. All local paths above are Atlas-relative. Local tracking parity uses existing tracking refs without fetch; the adjacent live comparison comes from GitHub's compare endpoint against the cloud default branch.

## Actions Samples, Releases, Protection, and Security Visibility

| Repository | Workflows | Run sample (success/failure/cancelled) | Sample health | Releases | Protection aggregate | Classic / rulesets | Dependabot | Secret scanning |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| ATLAS | 1 | 20 (17/3/0) | sample_mixed | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| DiscordOS | 2 | 20 (20/0/0) | sample_all_success | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| _stack | 0 | 0 (0/0/0) | no_runs_visible | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| cortex | 0 | 0 (0/0/0) | no_runs_visible | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| fawxzzy-fitness | 5 | 20 (0/20/0) | sample_mixed | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=1 |
| foundation | 1 | 20 (20/0/0) | sample_all_success | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| lifeline | 3 | 20 (20/0/0) | sample_all_success | none_visible (0) | protected | visible HTTP 200 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| mazer | 0 | 0 (0/0/0) | no_runs_visible | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| playbook | 14 | 20 (3/17/0) | sample_mixed | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |
| trove | 1 | 20 (20/0/0) | sample_all_success | none_visible (0) | not_protected | not_found HTTP 404 / visible count 0 | access_denied HTTP 403; open=unknown | visible; open=0 |

Lifeline `main` is the sole visible protected default: strict required status check `verify`, admin enforcement false, no visible required-review count, and no restrictions. The nine other default branches have classic HTTP 404 and zero visible repository rulesets. No endpoint disagreement or denial occurred on protection in this collection; the registry still encodes the required `conflicting`/`unknown` semantics for future runs.

The visible zero secret-scanning counts on the nine non-Fitness repositories are endpoint-specific observations only. The ecosystem does **not** have zero open secret alerts: Fitness has one open Critical alert. Dependabot security updates are reported disabled on all ten, while alert endpoints are access-denied; those facts remain separate.

## Mandatory Critical Security Truth

`fawxzzy/fawxzzy-fitness` has open secret-scanning alert 1, severity **Critical**, type `supabase_service_key`, display name `Supabase Service Key`, created `2026-04-17T04:17:11Z`, validity `unknown`, `publicly_leaked: true`, and `push_protection_bypassed: false`.

Safe location metadata only: commit `410efe6e8fa9a30b1c56362455397dfbf51b1942`, path `.env.local`, line `5`, blob `aa72c0dfece4ae7ec991ebe6f4f5f58ade7561d1`, URL <https://github.com/fawxzzy/fawxzzy-fitness/security/secret-scanning/1>.

Fitness product work remains blocked after the global opening gates until explicit operator-authorized containment, rotation, and verification. Rotation is mandatory if the key is or was live. Git history remediation is a separate explicit decision and is not automatic. This audit performed no Supabase, Fitness, Git-history, alert, settings, secret, or security mutation.

## Stale Readiness Note Reconciliation

| Historical observation in `tmp/github-control-plane-readiness-2026-07-11.md` | Disposition | Current evidence |
| --- | --- | --- |
| Ten public `fawxzzy` repositories, all defaulting to `main`, with admin-visible permissions | current | Live repository metadata reproduces the inventory, visibility, defaults, and permission projection. |
| Branch counts 52/11/5/1/6/4/23/28/20/5 in canonical order | current | Live branch endpoints reproduce every count. |
| Thirteen open PRs including Mazer #1/#34 and Trove #5 | current | Live PR reads return 13; the note's later ten-PR claim is superseded. |
| Later claim that Mazer and Trove PRs were no longer open | superseded | Live reads show Mazer #1/#34 and Trove #5 open. |
| No open issues enumerated | changed | ATLAS #49 and Trove #1 are open. |
| ATLAS and `_stack` historical heads | changed | ATLAS local/cloud default are `c31ff107...`; `_stack` local/cloud default are `5ea6b712...`. |
| DiscordOS 8 worktrees and `_stack` 23 worktrees | changed | Current counts are 12 and 40. |
| GitHub CLI unavailable | changed | The CLI is installed at the canonical local location and authenticated; it is not on this process's PATH, so the explicit local executable was used. |
| Security/dependency visibility not proven or zero open secrets | superseded/partly changed | Secret scanning is visible and Fitness has one Critical alert. Dependabot remains access_denied/unknown everywhere. |
| Empty combined status as Actions health evidence | unsupported | Direct workflow/run reads provide bounded samples; empty combined status is not health proof. |
| Historical closeouts prove current health | unsupported | No historical closeout is accepted as live health proof. |

## PR and Issue Disposition Queue

Allowed proposal vocabulary is `retain`, `review`, `close-candidate`, `merge-candidate`, and `superseded-candidate`. No item currently has enough proof for `close-candidate` or `superseded-candidate`; those values remain part of the deterministic contract. No disposition authorizes mutation.

| Repository | Work | Disposition | Evidence basis |
| --- | --- | --- | --- |
| ATLAS | pull_request #105 — Harden Fitness BrowserStack protected proof flow | retain | Registered worktree and stacked PR #106 preserve active context; current checks include one failed atlas-qa-llel result, so review and recovery remain required. |
| ATLAS | pull_request #106 — Stacked Mazer lock resync after BrowserStack proof branch | retain | Draft stacked PR targets PR #105's head branch; its reported QA check passes, but the dependency must resolve first. |
| ATLAS | pull_request #109 — Resync ATLAS after Mazer menu-generation updates | review | Draft PR has a passing QA check but currently conflicts with main and has no registered worktree proving current ownership. |
| ATLAS | issue #49 — Dispatcher Wave 1: `_stack vercel-health` implementation + independent root marker lane | review | Open dispatcher implementation issue lacks current terminal proof or a proven active owner. |
| _stack | pull_request #1 — docs: reduce path discipline warning residue | review | Historical draft currently conflicts with main and has no checks; age alone does not prove supersession. |
| lifeline | pull_request #23 — Lifeline: enforce appName contract parity | review | Historical draft has a passing check but currently conflicts with main; owner review must confirm contract relevance. |
| lifeline | pull_request #32 — docs: reduce path discipline warning residue | retain | Draft head is the active Lifeline checkout, mergeable clean, and its reported verify check passes. |
| lifeline | pull_request #33 — build(deps): bump actions/checkout from 6 to 7 in the github-actions group | merge-candidate | Non-draft Dependabot PR is mergeable clean and its reported verify check passes; merge remains separately authorized. |
| mazer | pull_request #1 — chore: reduce path discipline warning residue | review | Historical draft currently conflicts with main and has no checks; no terminal inference is supported. |
| mazer | pull_request #34 — Record hosted preview share proof | merge-candidate | Non-draft PR is mergeable clean; Mazer has no Actions workflows, so owner-side manual proof remains required. |
| playbook | pull_request #11 — docs: add phase-grid Boolean math core memo | merge-candidate | Non-draft one-commit documentation PR is mergeable clean; all reported checks pass or intentionally skip. |
| playbook | pull_request #12 — docs: add phase-grid Boolean evidence ledger | merge-candidate | Non-draft one-commit documentation PR is mergeable clean; all reported checks pass or intentionally skip. |
| playbook | pull_request #21 — docs: reduce path-discipline warning residue | retain | Draft head is the active Playbook checkout and checks pass, but it currently conflicts with main. |
| trove | pull_request #5 — docs: reduce path discipline warning residue | retain | Draft head is the active Trove checkout, mergeable clean, and its reported verify check passes. |
| trove | issue #1 — Track Vercel deployment platform incident for Trove | review | Historical Vercel incident needs current platform-status reconciliation before any closure decision. |

## CI Recovery Queue

### Playbook — demo contract synchronization

[Run 29185091723](https://github.com/fawxzzy/playbook/actions/runs/29185091723) is `demo-integration` on `main` at `aab5ad5b4a51f37f6426b0797080dfa565954788`. Composite CI and docs audit pass. Demo refresh dry-run integration fails because the demo doctor reports missing or invalid `docs/contracts/command-truth.json` and missing fact, interpretation, and narrative revision layers in `docs/PLAYBOOK_PRODUCT_ROADMAP.md`. Classification: **Playbook/demo contract synchronization**, not a generic runner failure.

### Fitness — contracts, runtime artifacts, and dependencies

[Run 29035579046](https://github.com/fawxzzy/fawxzzy-fitness/actions/runs/29035579046) is `atlas-contracts` on `main` at `e1ab7fbea979456380230c5459fdef6ae4c927e9`. `test:atlas-contracts` fails with `ERR_UNKNOWN_FILE_EXTENSION` for `src/lib/atlas-contracts.test.ts`.

[Run 29035579017](https://github.com/fawxzzy/fawxzzy-fitness/actions/runs/29035579017) is `CI` at the same head. Main lint, build, and large-file verification pass; Playbook clean-environment validation fails because required runtime artifacts are not written under `.playbook/` (the current missing artifact is `.playbook/last-run.json`).

The Fitness install reports **14 vulnerabilities: 3 moderate, 10 high, and 1 critical**, plus a deprecated **Next 14.2.5** warning. This is a separate dependency/security lane. No automatic dependency mutation is authorized.

## Remote Branch Cleanup Candidates

Candidates below are exact live branches whose comparison to the cloud default reports zero commits ahead after excluding default branches, active PR heads, protected branches, branches tied to active or preserved worktrees, and unresolved/not-fully-merged branches. This is evidence only; no deletion is authorized.

### ATLAS (37)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/archive-normalization-closeout` | `676751a50712e5ae7930a030a30dc284d8d4e22b` | behind | 0 | 1660 |
| `codex/atlas-owner-lane-separation-clean` | `f88658a1f9146f98f134baba87cd303405082d97` | behind | 0 | 288 |
| `codex/atlas-platform-v1-contracts` | `7e1f98904065c5eccf17e071496a68e48a2dd251` | behind | 0 | 1747 |
| `codex/atlas-qa-release-refresh-pr` | `7d11cbeef72ede446dcce5b3d875ed25b96bed47` | behind | 0 | 1707 |
| `codex/cortex-admission-planning` | `63e1fb40146464166fe697aa6ae44a82f5756b09` | behind | 0 | 1648 |
| `codex/cortex-ledger-wave5` | `3f237045651522dee15aa2d8f97f5e48a7d3bdbc` | behind | 0 | 1768 |
| `codex/cortex-operator-surface-wave4` | `7127bf57ee101ee8f59c44742a5adc6c38eeb7d5` | behind | 0 | 1774 |
| `codex/cortex-rail-seed-progression-r11` | `df9341392c578a00addb6360fac9d7851c59849b` | behind | 0 | 1765 |
| `codex/cortex-rail-seed-progression-r13` | `d5cbc0b1340f323ba13bc0a83312e002bdbe390d` | behind | 0 | 1759 |
| `codex/cortex-rail-seed-progression-r15` | `e97996a6b24f0d8901446f348c0edb8ea3789732` | behind | 0 | 1753 |
| `codex/cortex-rail-seed-progression-r17` | `2779dea37cb0b72de6dea908e6c05dcc3f254dec` | behind | 0 | 1747 |
| `codex/cortex-rail-seed-progression-r7` | `fb7bc448b4706f5de416112ace75163b9404a2c7` | behind | 0 | 1777 |
| `codex/cortex-rail-seed-progression-r9` | `c579f8a2a725ac7ad9eb830a8e560dc01552c8db` | behind | 0 | 1771 |
| `codex/cortex-receipt-interpretation-stack-consumption-wave10-clean` | `fa404f220587bb4734b3255dd62b7a9374f06f9a` | behind | 0 | 1728 |
| `codex/cortex-stack-consumption-pilot-wave7` | `9cc9070c5a722386dfd857b87f6b9de71360cfa0` | behind | 0 | 1756 |
| `codex/cortex-worker-prompt-contract-wave6` | `ca7e3c71a39754e29f0effaf7b611e302d927e22` | behind | 0 | 1762 |
| `codex/discord-moderation-receipt-clean` | `debc3f45ce21545bad80b8c8dfbfe613803206c8` | behind | 0 | 1686 |
| `codex/discord-update-workflow-memory` | `a385024cf2d8065758af2c4ac194cad96048d700` | behind | 0 | 1683 |
| `codex/final-verta-closeout-self-lock` | `15d4c2acd1725cd9414974113344247baf961230` | behind | 0 | 1664 |
| `codex/foundation-atlas-admission-alignment` | `051cfe6e6da6e229269d213098d098a176b82083` | behind | 0 | 1653 |
| `codex/foundation-pnpm-protected-refresh` | `3b9362d20e7ea07653446b1797202a8efb481124` | behind | 0 | 1692 |
| `codex/foundation-release-lock-refresh` | `5b26857d1e076875d868980752c0dbaae5954454` | behind | 0 | 1694 |
| `codex/near-100-marker-closeout-selector-pass-1` | `e44b4e0eec76c62f51f687154b9bf7d6f8dc2cc3` | behind | 0 | 1086 |
| `codex/playbook-release-lock-refresh` | `7e808b4b43b3402c5f7c34bda7ee34431922655e` | behind | 0 | 1703 |
| `codex/pnpm-protected-refresh` | `10d6b77901bb1bbbc96145ab475e4a7d8a2c5f96` | behind | 0 | 1705 |
| `codex/post-r20-cortex-artifact-normalization` | `e0c32ded21cdb2cdc81df640bdc2fb6bad85be15` | behind | 0 | 1720 |
| `codex/preserve-automation-governance-tranche-2026-06-05` | `d549abb0b42e47496977fc5f9db1d5ddd26477a2` | behind | 0 | 1268 |
| `codex/sparse-protected-stack-validation` | `82fb59f2091d0948923918de0c91d0529454dd02` | behind | 0 | 1699 |
| `codex/stack-progression-checkpoint` | `ce532ed6207cadafa5a44933e13b61b9e908bdf8` | behind | 0 | 1650 |
| `codex/validate-archive-registry-surfaces` | `92d6f65be6c445c185b9c0bf21b02d3bb7babde7` | behind | 0 | 1656 |
| `codex/verta-absorption-closeout-checkpoint` | `54e927ad24bfeba44c5bffe19d96685e8dbd3050` | behind | 0 | 1669 |
| `codex/verta-closeout-final-self-lock` | `34626bb284180bd22ed747bb08fd0a66bd8b6ec6` | behind | 0 | 1666 |
| `codex/verta-derivative-absorption-phase-gates` | `49511e51100ba0fa5c3bd136bd1e5d5eb9e20cca` | behind | 0 | 1679 |
| `codex/verta-gate-final-lock-refresh` | `477edaa4d1a7dbf88636fb1f72c3f98c7c1670d3` | behind | 0 | 1671 |
| `codex/verta-gate-stack-lock-refresh` | `017d9180b15d11a8b7516dd53ac5387a6edac7fb` | behind | 0 | 1673 |
| `codex/verta-lookup-stack-lock-refresh` | `7db98d0d91554f23128c1f5ea63aa10540dd49d7` | behind | 0 | 1675 |
| `codex/verta-post-merge-stack-lock-refresh` | `b052ec063aded2fc41f6cdae77cb5bc507400e95` | behind | 0 | 1677 |

Exclusions: default 1; active PR 3; protected 0; registered/preserved worktree 0; not fully merged 11; unresolved 0.

### DiscordOS (3)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/discordos-mazer-board-cards` | `87f291f4eab60263b82a0c8790c64a7cd25ae5a0` | behind | 0 | 13 |
| `codex/message-command-poll-status` | `76b699269b724070f548ca7841d36ec1505727f8` | behind | 0 | 36 |
| `codex/path-discipline-warning-slice-discordos` | `f58432152d3a3d072c0f43d4d1b903d0bde9f133` | behind | 0 | 179 |

Exclusions: default 1; active PR 0; protected 0; registered/preserved worktree 6; not fully merged 1; unresolved 0.

### _stack (1)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/preserve-stack-packaging-tranche-2026-06-05` | `eb1f7c49e4e887e52b465b3fdf4d9ab25affbc57` | behind | 0 | 26 |

Exclusions: default 1; active PR 1; protected 0; registered/preserved worktree 1; not fully merged 1; unresolved 0.

### cortex (0)

None.

Exclusions: default 1; active PR 0; protected 0; registered/preserved worktree 0; not fully merged 0; unresolved 0.

### fawxzzy-fitness (2)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/fitness-main-progression-summary-reapply` | `fa30c13d18a8b72c8d8ebd6cdeb9990610dc04a2` | behind | 0 | 40 |
| `codex/per-day-exercise-templates` | `6d75c1814d670e146e2c3cd8a2e3f20c3de33fbf` | behind | 0 | 96 |

Exclusions: default 1; active PR 0; protected 0; registered/preserved worktree 0; not fully merged 3; unresolved 0.

### foundation (3)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/wave-2a-2-proof` | `ad78ea472a902a6fca7da8b55952f88d718a60e9` | behind | 0 | 7 |
| `codex/wave-2a-3-proof` | `2f7f22bf84968508357ea55c626d68e2580be833` | behind | 0 | 6 |
| `codex/wave-2a-4-proof` | `36ac2970c77160c4e7efdcc881eb3b53f3b3182f` | behind | 0 | 5 |

Exclusions: default 1; active PR 0; protected 0; registered/preserved worktree 0; not fully merged 0; unresolved 0.

### lifeline (16)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/canary-verify-contract` | `a81914d6a849e056ae4d7ea703a3a16be97a5e70` | behind | 0 | 38 |
| `codex/lifeline-hermetic-validation-wave1` | `5ce5a8ea2f6095912f6a6e69c43ba52de278459d` | behind | 0 | 47 |
| `codex/lifeline-operator-evidence` | `bdb50fcce1bcf0742a74b8fcbd783f7b68bd65bc` | behind | 0 | 33 |
| `codex/lifeline-proof-pass-fixture-expansion` | `6fa90955d19dbebc4216c5b02107cbd1e616c67d` | behind | 0 | 45 |
| `codex/lifeline-release-appname-path-hardening` | `89357af70fc103137bd5f46c76d3c81549ba64fc` | behind | 0 | 16 |
| `codex/lifeline-release-cli-surface` | `16b10ef43b2d073ccf4ef124ec3bf9c18a6950a4` | behind | 0 | 20 |
| `codex/lifeline-release-phase-hooks` | `35297d6aea35a28427251614e0289a2412840b8d` | behind | 0 | 19 |
| `codex/lifeline-release-receipt-schema-parity` | `d3d8496d65d00b715c721fc5c4012d524c8089ae` | behind | 0 | 1 |
| `codex/lifeline-release-replay-verification` | `4589b4f332247b32e01931907f803e5ea5991e34` | behind | 0 | 13 |
| `codex/lifeline-release-safety-closeout-checkpoint` | `a6079866da6f280c14f279fa8f333e9f02c7b958` | behind | 0 | 3 |
| `codex/lifeline-required-verify-governance` | `893da3637fdd5f4c98b8839d51e7fda77c1abd36` | behind | 0 | 40 |
| `codex/lifeline-rollback-rehearsal-evidence` | `e4de3eba46064d1d404497ae936ba1497ec7f2bb` | behind | 0 | 25 |
| `codex/lifeline-topology-contract-intake` | `57cef1b881d0785e8a4c32c1920c3fcd62ab6677` | behind | 0 | 22 |
| `codex/lifeline-wave1-release-safety` | `34ce04c34c43991c0bc7a6c6e2d91ef2a002b683` | behind | 0 | 12 |
| `codex/lifeline-wave2-release-safety` | `ecce13c960a022a835270846bcc73f010ec4c1c5` | behind | 0 | 7 |
| `codex/lifeline-wave3-rollback-confidence` | `cee62ab28a4b1e0a6b6ad6f42e744785de4ccacb` | behind | 0 | 5 |

Exclusions: default 1; active PR 3; protected 0; registered/preserved worktree 0; not fully merged 3; unresolved 0.

### mazer (2)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/legacy-web-port-truth` | `a7cb12d281e450a6d8f4ea3a766378cacb7e1e3d` | behind | 0 | 164 |
| `codex/mazer-playbook-path-references` | `4719850977a5726ee1cf3a788f6dbe2f7827f5b8` | behind | 0 | 215 |

Exclusions: default 1; active PR 2; protected 0; registered/preserved worktree 6; not fully merged 17; unresolved 0.

### playbook (15)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/changelog-generator` | `431e83e143717fa8ad792fd6f3dc72074d20195c` | behind | 0 | 34 |
| `codex/playbook-baseline-finding-identity` | `90217f423e91306cbf9cce93a4d5095ee8a2f572` | behind | 0 | 51 |
| `codex/playbook-lint-debt-closeout` | `0a562d337f2c354c1977df7441abbfe598362c83` | behind | 0 | 5 |
| `codex/playbook-sarif-output` | `6d893d0245436a2e670c0decf18bb2c8b1a9aab0` | behind | 0 | 49 |
| `codex/playbook-sustain-docs-audit` | `4f1d95529f373eaa287096098092204c14215576` | behind | 0 | 1 |
| `codex/playbook-verify-baseline-hygiene` | `136779b68837624733e6b2e0676df3e645ca68e9` | behind | 0 | 53 |
| `codex/verta-derivative-doctrine-closeout` | `52537b0af23cf5ef8632f0eb9f59afa7c2e440f0` | behind | 0 | 14 |
| `codex/verta-derivative-doctrine-patterns` | `239b9ee4457f17c4186126880f2639470d2f8cec` | behind | 0 | 18 |
| `codex/verta-doctrine-pattern-lookup` | `c0f039862a6795d6abba0d7dc24bbd06742e8917` | behind | 0 | 12 |
| `codex/verta-gate-path-trust-hardening` | `d88996f2222fc626565e8549a86e065536231e2b` | behind | 0 | 8 |
| `codex/verta-seam-gate-validator` | `e0c5824100df66602ddcfc5dcd96722069ba40cf` | behind | 0 | 10 |
| `codex/workflow-pack-environment-bridge-dry-run-executor` | `7b62d6598e2f67cae62f9210c93e65eadbc4754f` | behind | 0 | 19 |
| `codex/workflow-pack-environment-bridge-engine` | `52ee1b57f46a64838d1df9ebf2cd30355fa45d9d` | behind | 0 | 31 |
| `codex/workflow-pack-environment-bridge-executor-contract` | `91dafb005ddb8bba50bf85ca26a3f41fc7ec2597` | behind | 0 | 25 |
| `codex/workflow-pack-environment-bridge-planner` | `058cc68aaa6963bc37412c4d5c5d77f9d247c448` | behind | 0 | 28 |

Exclusions: default 1; active PR 3; protected 0; registered/preserved worktree 0; not fully merged 1; unresolved 0.

### trove (1)

| Branch | Head | Compare status | Ahead | Behind |
| --- | --- | --- | ---: | ---: |
| `codex/trove-pilot-release-cutover` | `75c3119e2385990a0f4a157bf22442b941cfbdd7` | behind | 0 | 2 |

Exclusions: default 1; active PR 1; protected 0; registered/preserved worktree 0; not fully merged 2; unresolved 0.

## Local Worktree Cleanup Candidates

Every non-primary worktree is inventoried separately with `retention_class UNKNOWN`, `removal_safe: false`, and no durable removal receipt. Paths are Atlas-relative; external worktrees use non-machine-specific locators. No worktree may be deleted, moved, archived, or cleaned from this evidence.

| Repository | Atlas-relative path or external locator | Branch | Head | Retention class |
| --- | --- | --- | --- | --- |
| ATLAS | `external-worktree:b0r2` | `codex/atlas-vnext-wave1b0-r2-canonical-writer-proof-recovery` | `b87ab5ed21312d36d8e256e62e0b95e124fed9e4` | UNKNOWN |
| ATLAS | `external-worktree:pr108-ci-repro` | `null` | `05df178e07b0bdcc6d5b6b3505268df4985c275e` | UNKNOWN |
| ATLAS | `tmp/atlas-browserstack-fix` | `codex/atlas-browserstack-provider-capture` | `274fab0a3ed7cda865e33c93815e4f1102e16870` | UNKNOWN |
| DiscordOS | `d` | `codex/mazer-ai-corpus-board` | `b1f852f33aea69a97734c9c16f06cca713279d8c` | UNKNOWN |
| DiscordOS | `d2` | `codex/mazer-ai-metric-board` | `ce8998f60be471b593a93db97645ad80934b552c` | UNKNOWN |
| DiscordOS | `d3` | `codex/mazer-board-epic-reconciliation` | `41455a3013315638030d59cea66bc061552815dd` | UNKNOWN |
| DiscordOS | `d4` | `codex/mazer-ui-evidence-board-update` | `41fffe73b9ea07fa62ec67e10b14dc854028708a` | UNKNOWN |
| DiscordOS | `d5` | `codex/mazer-player-input-evidence` | `6f9cd30e049c04f9bbb3dd43aa4cc8e8ee79aaa7` | UNKNOWN |
| DiscordOS | `d6` | `codex/mazer-play-loop-evidence` | `69b8d95e52f9d0b17f39d744f56e7bcd89c4c2ad` | UNKNOWN |
| DiscordOS | `d7` | `codex/mazer-world-turn-evidence` | `015b92afe5ce2f73b25d2c5cae80fe3e5ca1d234` | UNKNOWN |
| DiscordOS | `runtime/w/d/d2r2` | `codex/d2r2` | `5a87166b001766ba40ba1d152824398f13788443` | UNKNOWN |
| DiscordOS | `runtime/w/d/d2r2-2` | `codex/d2r2-2` | `5a87166b001766ba40ba1d152824398f13788443` | UNKNOWN |
| DiscordOS | `runtime/w/d/d2r5` | `codex/d2r5` | `5a87166b001766ba40ba1d152824398f13788443` | UNKNOWN |
| DiscordOS | `runtime/w/d/d2r6` | `codex/d2r6` | `5a87166b001766ba40ba1d152824398f13788443` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence` | `codex/atlas-operational-prep-codex-cli-capability-convergence` | `c2afaafe4f73c678cc4d467af090fefd0766f193` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r2` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r2` | `c2afaafe4f73c678cc4d467af090fefd0766f193` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r3` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r3` | `c2afaafe4f73c678cc4d467af090fefd0766f193` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r4` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r4` | `c2afaafe4f73c678cc4d467af090fefd0766f193` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-codex-cli-capability-convergence-r5` | `codex/atlas-operational-prep-codex-cli-capability-convergence-r5` | `6e96d1571121a30c668b5c6f9d283ca316912126` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-r1-discordos-owner-adapter` | `codex/atlas-operational-prep-d0-r1-discordos-owner-adapter` | `2127af207370cacf8752fd4f13c6545ea49bb503` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-s0-worktree-safe-brand-verifier` | `codex/atlas-operational-prep-d0-s0-worktree-safe-brand-verifier` | `0b91367158f09ca3ea007752678142cde9fb7653` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-s1-r1-scoped-brand-proof-recovery` | `codex/atlas-operational-prep-d0-s1-r1-scoped-brand-proof-recovery` | `1c063d53f263382b2dda6b5629b993d7e534d02e` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d0-s1-scoped-brand-verification-recovery` | `codex/atlas-operational-prep-d0-s1-scoped-brand-verification-recovery` | `0b91367158f09ca3ea007752678142cde9fb7653` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r0-stack-discordos-runtime-receipt-repair` | `codex/atlas-operational-prep-d2-r0-stack-discordos-runtime-receipt-repair` | `baef0dab99eacc98a8037be6df9b5af009a26a0b` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r2-stack-worktree-path-budget` | `codex/atlas-operational-prep-d2-r2-stack-worktree-path-budget` | `9504224ee5ae99c3b0f6f39c9b3c961a4562204b` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r3-stack-permission-precedence-repair` | `codex/atlas-operational-prep-d2-r3-stack-permission-precedence-repair` | `d1fdae5c7d0a3482f0d53ac51f90dd024f418ebc` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-d2-r4-stack-verified-no-change-contract` | `codex/atlas-operational-prep-d2-r4-stack-verified-no-change-contract` | `5ea6b712b91a691689b619addb8f8ba649126661` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c0-r1-owner-path-verifier-recovery` | `codex/atlas-operational-prep-packet-c0-r1-owner-path-verifier-recovery` | `6e96d1571121a30c668b5c6f9d283ca316912126` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c0-r2-diff-addressable-proof-recovery` | `codex/atlas-operational-prep-packet-c0-r2-diff-addressable-proof-recovery` | `a7cf3ab4632a12a61150beee0fa97f90221b2dc5` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c0-stack-owner-path-truth` | `codex/atlas-operational-prep-packet-c0-stack-owner-path-truth` | `6e96d1571121a30c668b5c6f9d283ca316912126` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c1-r1-stack-playbook-adoption-recovery` | `codex/atlas-operational-prep-packet-c1-r1-stack-playbook-adoption-recovery` | `0b91367158f09ca3ea007752678142cde9fb7653` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c1-s0-stack-playbook-evidence-admission` | `codex/atlas-operational-prep-packet-c1-s0-stack-playbook-evidence-admission` | `2446bfc2513fe509e88e6a8f84c77079696875fd` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-c1-stack-playbook-adoption` | `codex/atlas-operational-prep-packet-c1-stack-playbook-adoption` | `a7cf3ab4632a12a61150beee0fa97f90221b2dc5` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-operational-prep-packet-d0-discordos-owner-adapter` | `codex/atlas-operational-prep-packet-d0-discordos-owner-adapter` | `0b91367158f09ca3ea007752678142cde9fb7653` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-r1-stack-runtime-salvage` | `codex/atlas-vnext-wave1a-r1-stack-runtime-salvage` | `fc9ec24ab3e37e4bc651342dbd0b765cda680b38` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-stack-runtime-bootstrap` | `codex/atlas-vnext-wave1a-stack-runtime-bootstrap` | `7ca8a81acb71c935adabd345dff3e3bcbbedba7c` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-stack-runtime-bootstrap-2` | `codex/atlas-vnext-wave1a-stack-runtime-bootstrap-2` | `7ca8a81acb71c935adabd345dff3e3bcbbedba7c` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1a-stack-runtime-bootstrap-3` | `codex/atlas-vnext-wave1a-stack-runtime-bootstrap-3` | `7ca8a81acb71c935adabd345dff3e3bcbbedba7c` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-canonical-workspace-writer` | `codex/atlas-vnext-wave1b0-canonical-workspace-writer` | `fc9ec24ab3e37e4bc651342dbd0b765cda680b38` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-canonical-workspace-writer-2` | `codex/atlas-vnext-wave1b0-canonical-workspace-writer-2` | `fc9ec24ab3e37e4bc651342dbd0b765cda680b38` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-canonical-workspace-writer-3` | `codex/atlas-vnext-wave1b0-canonical-workspace-writer-3` | `fc9ec24ab3e37e4bc651342dbd0b765cda680b38` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-r2-canonical-writer-proof-recovery` | `codex/atlas-vnext-wave1b0-r2-canonical-writer-proof-recovery` | `fc9ec24ab3e37e4bc651342dbd0b765cda680b38` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-r3-canonical-writer-recovery` | `codex/atlas-vnext-wave1b0-r3-canonical-writer-recovery` | `93821b1924755eb59acae118e009865ccf469fe7` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b0-r4-canonical-writer-recovery` | `codex/atlas-vnext-wave1b0-r4-canonical-writer-recovery` | `dc405b30251672c388e78baca43274c97feee897` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r2-canonical-directory-digest-fix` | `codex/atlas-vnext-wave1b1-r2-canonical-directory-digest-fix` | `dc405b30251672c388e78baca43274c97feee897` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r3-canonical-directory-digest-recovery` | `codex/atlas-vnext-wave1b1-r3-canonical-directory-digest-recovery` | `32c55a5eefe4ebe983b2f65f68aa795a55ecf1ab` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r4-canonical-executable-resolution-fix` | `codex/atlas-vnext-wave1b1-r4-canonical-executable-resolution-fix` | `32c55a5eefe4ebe983b2f65f68aa795a55ecf1ab` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r5-canonical-executable-resolution-recovery` | `codex/atlas-vnext-wave1b1-r5-canonical-executable-resolution-recovery` | `038871832df78642016356ecd191b78f970a2bf5` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r6-registered-owner-worktree-preservation` | `codex/atlas-vnext-wave1b1-r6-registered-owner-worktree-preservation` | `038871832df78642016356ecd191b78f970a2bf5` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r7-registered-owner-worktree-proof-recovery` | `codex/atlas-vnext-wave1b1-r7-registered-owner-worktree-proof-recovery` | `038871832df78642016356ecd191b78f970a2bf5` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r8-registered-owner-worktree-network-recovery` | `codex/atlas-vnext-wave1b1-r8-registered-owner-worktree-network-recovery` | `038871832df78642016356ecd191b78f970a2bf5` | UNKNOWN |
| _stack | `repos/_stack/.codex/worktrees/atlas-vnext-wave1b1-r9-registered-owner-worktree-supported-model-recovery` | `codex/atlas-vnext-wave1b1-r9-registered-owner-worktree-supported-model-recovery` | `c2afaafe4f73c678cc4d467af090fefd0766f193` | UNKNOWN |
| _stack | `tmp/_stack-mazer-operator-fix` | `codex/mazer-operator-path-fix-clean` | `a899a13ee45ab5bf248946f33c65e9a9c12c1774` | UNKNOWN |
| fawxzzy-fitness | `tmp/fawxzzy-fitness-discord-hotfix` | `codex/discord-message-command-recovery` | `81919c7512262d12825ee3597289b6d4abc8e49d` | UNKNOWN |
| mazer | `input4` | `codex/player-input-movement-correctness` | `9759ce22f68746ca73a294695fb28449cfc6a76e` | UNKNOWN |
| mazer | `m2` | `codex/ai-metric-contract-parity` | `e11ab6e5c677f1f8d2859be310122f3c73b7a605` | UNKNOWN |
| mazer | `playloop` | `codex/play-mode-perpetual-loop` | `e9647e77b48e71b4df7b8dd7c14d3cc2652b3f61` | UNKNOWN |
| mazer | `tmp/worktrees/mazer-ai-run-corpus-quality-calibration` | `codex/ai-run-corpus-quality-calibration` | `05c2e51158a6556acb725ad42fbe8f992677fef9` | UNKNOWN |
| mazer | `tmp/worktrees/mazer-viewport-layout-contract` | `codex/viewport-layout-contract` | `ff6139ba8bef85f74d0c1bd72a2b18f1b3087dac` | UNKNOWN |
| mazer | `turnlive` | `codex/world-turn-live-integration` | `8ced175c65cfb36bb057cf25e93f59819c57803b` | UNKNOWN |
| mazer | `turnsim` | `codex/turn-synchronous-world-simulation` | `cf94ede0127a802108c7261556a61af4c9f5df8a` | UNKNOWN |
| mazer | `ui3` | `codex/cross-platform-ui-followup` | `a27324a422809c577b29e66a53b84ed94c6cb163` | UNKNOWN |

## Cortex Boundary Decision

`fawxzzy/cortex` is a live remote-only repository (`main` at `495808fde487b3bdca2de283ff53f748b0b84630`, one branch) while `runtime/cortex` is the canonical embedded, root-owned subsystem declared by `stack.yaml`. An explicit operator decision must choose owner-repo adoption, reference/archive treatment, or continued separation. Do not clone, move, or synchronize either side implicitly.

## Stream Remote Decision

Stream is clean local-only at `repos/stream`, `main` / `43769ba86d4c6ebc419ab9e7847c3843460a094f`, with no origin or upstream. An explicit operator decision must choose publishing a `fawxzzy` remote, retaining local-only status, or archival. Do not create or attach a remote automatically.

## Integration Plan

- `_stack`: normalize immutable GitHub repository, ref, PR, workflow, run, release, protection, security-visibility, and cleanup-candidate facts; emit idempotent events correlated by repository, SHA, branch, PR/issue, run, deployment, job, and receipt IDs.
- Atlas: version registry contracts, freshness windows, evidence confidence, access failures, opening/closing audits, correlated receipts, and marker-audit gates without allowing discoveries to inflate marker percentages.
- DiscordOS: consume only admitted `_stack` events through the accepted single writer; map failures, releases, cleanup review, and owner blockers onto boards/Updates with idempotency and live readback receipts.
- Vercel: correlate preview/production deployment IDs and Git SHAs with GitHub runs and Atlas receipts. Production deploy/promotion remains separately approval-gated per project.
- Supabase: correlate migrations/functions/project evidence to Git SHAs and receipts without storing secrets. Fitness alert containment/rotation/verification remains an explicit operator-authorized security lane; no live-data mutation follows from this integration.

## Phases

### Phase 1 — Inventory

Automate stable repository/component identity, timestamps, access states, stack/lock/inventory reconciliation, and deterministic registry generation.

### Phase 2 — Parity monitoring

Keep local tracking parity, live cloud-default comparison, branch topology, and worktree registration separate and freshness-stamped.

### Phase 3 — Actions monitoring

Project bounded workflow/run health, exact failure families, owner recovery queues, rerun lineage, and proof-backed closure.

### Phase 4 — PR/issue hygiene

Maintain allowed disposition, checks, mergeability, stacked dependencies, owner, and terminal reconciliation without automatic mutation.

### Phase 5 — Releases/security

Project releases, classic protection, rulesets, Dependabot, secret scanning, and access-denied/unknown states with owner decisions.

### Phase 6 — Cleanup

Recompute exclusions immediately before any separately authorized deletion/removal and write idempotent pre/post receipts.

### Phase 7 — DiscordOS projections

Route admitted `_stack` GitHub events to boards/Updates with single-writer enforcement and readback.

## Rules

- **RULE — Endpoint-specific absence is not zero.** Preserve access-denied, disabled, empty, not-found, conflicting, and unknown as distinct states.
- **RULE — Cleanup evidence expires.** Requery default, active PR, protected/ruleset, worktree, merge, and unresolved exclusions immediately before an authorized cleanup packet.
- **RULE — Security authority stays separate.** A registry may expose safe alert metadata but never retrieve values, rotate credentials, rewrite history, dismiss alerts, or resume Fitness without explicit authority.
- **RULE — Discoveries become named lanes.** They never inflate the Atlas Full-System Re-evaluation marker.

## Patterns

- **PATTERN — Local-first execution with live cloud correlation.** Local Git proves checkout/worktree facts; GitHub proves cloud state; Atlas preserves meaning; `_stack` and DiscordOS project correlated events.
- **PATTERN — Two-layer parity.** Tracking-ref parity without fetch and live default-branch comparison answer different questions and remain separate.
- **PATTERN — Security-safe projection.** Carry type, state, severity, timestamps, booleans, safe location metadata, and alert URL—never a secret value.

## Failure Modes

- **FAILURE MODE — False-zero security.** Treating HTTP 403 or disabled Dependabot settings as zero alerts hides unknown exposure.
- **FAILURE MODE — Main-only health.** A default SHA or empty combined status hides branch divergence, failed scheduled Actions, and active worktrees.
- **FAILURE MODE — Uncorrelated cleanup.** Age or merged appearance alone can delete the only durable owner-lane state.
- **FAILURE MODE — Historical promotion.** Copying failed-run artifacts or stale readiness notes without live revalidation converts old evidence into false authority.
- **FAILURE MODE — Generic CI labeling.** Runner-failure language obscures Playbook/demo contract synchronization and Fitness loader/runtime-artifact root causes.

## Automation Opportunities

- Add a deterministic read-only collector and semantic agreement test for audit/registry/initiative security, CI, ordering, and resume-gate facts.
- Emit `_stack` GitHub facts/events with freshness, endpoint status, URL, SHA, branch, PR/run/release IDs, and correlated Atlas receipt IDs.
- Add parity and Actions watchers that open named recovery lanes only on state change and never rerun workflows automatically.
- Generate review-only cleanup packets with exclusion proofs, expiry, retention class, and explicit mutation authority.
- Project accepted events to DiscordOS boards/Updates with idempotency keys and readback.

## Governance Gaps

- Nine default branches lack visible classic protection and visible repository rulesets; Lifeline policy is not yet a stack-wide baseline.
- No releases are visible across the ten repositories; release intent, tag policy, and evidence contracts need owner decisions.
- Dependabot alert visibility is access_denied/unknown everywhere, while security updates report disabled.
- Fitness has an open Critical `supabase_service_key` alert and a separate dependency/security lane.
- `_stack` lacks the complete normalized GitHub event/receipt family; DiscordOS lacks accepted end-to-end GitHub projection/readback proof.
- Cortex remote ownership and Stream publication boundaries remain unresolved.
- ATLAS and `_stack` published inventory heads, plus the `_stack` lock pin, are stale and require a separate projection-refresh lane.

No completion percentage is assigned. Historical closeout material does not prove current health.
