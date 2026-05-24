# Core Pattern Convergence Matrix

Date: 2026-05-24
Lane: Core Pattern Convergence
Mode: docs-only convergence matrix
Status: baseline matrix recorded

## Goal

Make the strongest reusable rules, patterns, and failure modes visible across the stack so they stop living as isolated local habits.

This pass does not migrate Cortex runtime ownership, implement Playbook features, add `_stack` automation, or change repo runtime behavior. It defines where the strongest patterns came from, where they already apply, and where they should spread next.

## Reading Rule

Each row answers:

1. what the reusable idea is
2. where it came from
3. why it matters
4. where it already applies
5. where it should apply next
6. which surface should own the next proof or automation step

Owner labels:

- `ATLAS`
- `_stack`
- `Playbook`
- `Lifeline`
- `Foundation`
- `Cortex`
- `Fitness`
- `Discord OS`
- `QA/LLEL`

Automation labels:

- `yes`
- `later`
- `no`

Doctrine labels:

- `playbook_now`
- `atlas_only_for_now`
- `later`

## Matrix

| Pattern name | Origin lane | Class | Why it matters | Already applies | Apply next | Owning surface | Verification path | Automation candidate | Playbook doctrine now | Cortex planning context | `_stack` automation path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| owner repo truth over `tmp` or worktree truth | Canonical Repo Restoration, Tmp Dependency Elimination | Rule | Prevents wrong-repo and wrong-path execution truth | Fitness canonical repo reset, root routing doctrine, duplicate-surface closeout | Trove, Mazer, Foundation, future recovery lanes | ATLAS, `_stack`, Fitness | canonical-path receipts, root validation, stack lock pin alignment | later | playbook_now | yes | yes |
| preserve or classify before delete | Archive Normalization, Duplicate Surface Decommission | Pattern | Prevents destructive cleanup from erasing evidence or active ownership | archive routing, duplicate surface inventory, worktree disposal receipts | future branch cleanup, residue closeout, installer retention policy | ATLAS, Lifeline | inventory plus disposal receipt or retention decision | later | playbook_now | yes | later |
| one owner seam before execution | Unified Operator Entrypoint, Branch & Worktree Normalization | Rule | Eliminates mixed-root execution and ambiguous authority | root routing, owner repo worktree policy, deploy entrypoint docs | future multi-repo automation, Cortex task admission, repo handoff tooling | ATLAS, `_stack`, Cortex | owner-surface declaration plus named branch or worktree and receipt | yes | playbook_now | yes | yes |
| no Discord post before proof | Unified Release and Update Handoff, Unified QA Proof Handoff, Discord OS Boundary | Rule | Keeps public communication downstream of verified truth | Fitness updates workflow, release ledger doctrine, feedback closeout maps | Discord publication automation, release bot guardrails, non-Fitness product updates | Discord OS, ATLAS, QA/LLEL | proof receipt plus release ledger plus publish receipt | yes | playbook_now | yes | later |
| no manual deploy by default | Manual Deploy Exception Burn-Down | Rule | Stops direct CLI deploys from bypassing governed orchestration | Fitness deploy authority clarification, burn-down checkpoint | Trove and Mazer Git auto-deploy documentation, future service deploy lanes | `_stack`, ATLAS | deploy authority receipts, stack lock decisions, validation | later | playbook_now | yes | yes |
| `_stack` owns deploy authority | Manual Deploy Exception Burn-Down, Unified Release Handoff | Rule | Creates one execution owner for preview and production deploys | Fitness today, Trove and Mazer deploy wrappers, release/deploy handoff map | broader app portfolio, branch deployment proof, service onboarding | `_stack` | preflight scripts, deploy runbooks, release receipts | yes | playbook_now | yes | yes |
| repo-local commands prepare and verify, not deploy | Fitness Release Authority Clarification | Rule | Separates local build or release prep from production authority | Fitness README and release docs, release ladder map | Trove and Mazer docs, future repos entering `_stack` | owner repos, `_stack` | repo docs plus deploy checkpoint receipt | later | playbook_now | yes | later |
| receipt-backed closeout | Unified Workflow Convergence, Playbook Core Pattern Handoff | Pattern | Prevents completion claims from living only in chat | lane checkpoints, stack lock decisions, QA receipts, release notes | Discord publication receipts, doctrine extraction passes, automation receipts | ATLAS, Playbook | receipt exists, marker move is justified, validation passes | yes | playbook_now | yes | later |
| fail-closed identity guards | Manual Deploy Exception Burn-Down | Rule | Blocks deploys when local identity drifts from approved project truth | Trove and Mazer Vercel identity preflights, Fitness deploy posture | other hosted surfaces, future secrets or connector identity checks | `_stack` | preflight pass and negative-case proof | yes | playbook_now | yes | yes |
| canonical source -> generated outputs -> consumer sync | Brand Asset Canonicalization, Preview Cache and Surface Consistency | Pattern | Separates source truth from generated artifacts and consumers | ATLAS branding canon, `_stack` launcher, Trove and Fitness icon sync | broader preview verification, share images, remote cache checks | ATLAS, owner repos | hash receipts, live-surface pass, remote verification plan | later | playbook_now | yes | later |
| no `tmp` fallback for source truth | Canonical Repo Restoration, Brand lanes, QA proof maps | Rule | Prevents emergency fallback paths from becoming hidden production truth | Fitness icon sync, preview verification docs, root doctrine | release packaging, preview verification, future recovery docs | ATLAS, Fitness, QA/LLEL | receipts explicitly confirming no `tmp` fallback | later | playbook_now | yes | later |
| clean worktree before lane execution | Branch & Worktree Normalization, Operator Ladder | Rule | Reduces mixed diffs and false ownership inside narrow lanes | worktree normalization doctrine, repo-lane routing, `_stack` preflight assumptions | future automation, sub-agent task routing, release prep gates | ATLAS, `_stack` | git status check plus declared ownership boundary | yes | playbook_now | yes | yes |
| branch name is metadata, diff and ownership are truth | Branch & Worktree Normalization | Failure Mode | Prevents over-trusting branch labels while ignoring actual scope | normalization inventory, preservation routing, worktree closeout | future parallel worker routing and lane packaging | ATLAS, Playbook | inventory review, owner repo mapping, diff classification receipt | later | playbook_now | yes | later |
| repeated AI tasks become automation candidates | AI Repetition-to-Automation, Operator Ladder, Playbook Core Pattern Handoff | Pattern | Converts repeated chat work into durable operator surfaces | updates posting, receipt packaging, validation summaries, doctrine extraction discussions | `_stack` commands, Playbook checklist surfaces, Discord publication helpers | ATLAS, `_stack`, Playbook, Discord OS | repetition evidence plus owner and rollback classification | yes | playbook_now | yes | yes |
| verify -> plan -> apply -> verify | Playbook origin doctrine | Pattern | Keeps diagnosis, mutation, and trust renewal separate | Playbook notes, convergence maps, remediation framing | `_stack` operator flows, QA gate ladders, Discord publication gates | Playbook, `_stack`, QA/LLEL | command and receipt sequence preserved end-to-end | later | playbook_now | yes | later |
| local proof before release or public update | Unified QA Proof Handoff, Release Handoff | Pattern | Forces readiness evidence to exist before deploy or publication | Fitness QA/LLEL lanes, local proof receipts, update rules | Trove, Mazer, future web and service repos | QA/LLEL, owner repos, ATLAS | local proof receipt plus release-readiness receipt | later | playbook_now | yes | later |
| feedback or update lessons become doctrine only after bounded evidence | Discord OS Boundary, Playbook Core Pattern Handoff | Rule | Stops chat reactions from becoming stack truth without receipts | feedback forum workflow, update-post classification fixes, forum audit comments | future Discord OS extraction review, publication automation | Discord OS, ATLAS, Playbook | audit comment, export, or receipt linked before doctrine promotion | later | playbook_now | yes | later |

## By Owner Surface

### ATLAS

ATLAS should own:

- cross-lane pattern visibility
- convergence state
- marker movement justification
- stack-lock consequence
- root doctrine and pause checkpoints

ATLAS should verify with:

- `docs/ops/*`
- `docs/PLAYBOOK_NOTES.md`
- `stack.lock.yaml`
- root validation

### `_stack`

`_stack` should own:

- deploy authority
- fail-closed identity preflights
- future repeated operator-flow automation
- entrypoint discipline for shared execution

`_stack` should verify with:

- operator-surface tests
- preflight scripts
- deploy runbooks
- stack lock decisions

### Playbook

Playbook should own:

- reusable governance wording
- verify or plan or apply doctrine
- promoted rules, patterns, and failure modes
- reusable command or checklist semantics after evidence stabilizes

Playbook should verify with:

- doctrine promotion receipts
- command truth separation
- repeated cross-lane applicability

### Cortex

Cortex should consume:

- planning context
- convergence summaries
- owner and evidence boundaries
- automation-candidate queues

Cortex should not yet own:

- runtime mutation
- doctrine promotion
- deploy authority

### Owner repos and proof lanes

Fitness, Discord OS, and QA/LLEL remain the strongest current proof lanes for:

- feedback workflow
- proof-before-publication
- release-ledger dependency
- local proof before release

## First Recommended Next Applications

1. Apply `receipt-backed closeout` and `repeated AI tasks become automation candidates` to the updates and release-publication workflow.
2. Apply `clean worktree before lane execution` and `one owner seam before execution` to future multi-agent or parallel-lane routing.
3. Apply `feedback or update lessons become doctrine only after bounded evidence` to Discord OS extraction review.
4. Apply `canonical source -> generated outputs -> consumer sync` to the eventual remote preview and unfurl verification lane.
5. Apply `repo-local commands prepare and verify, not deploy` to Trove and Mazer docs if their local release surfaces widen.

## What Belongs In Playbook Now

Promote now:

- owner repo truth over `tmp` truth
- preserve or classify before delete
- one owner seam before execution
- no Discord post before proof
- no manual deploy by default
- `_stack` owns deploy authority
- repo-local prepare or verify versus deploy authority split
- receipt-backed closeout
- fail-closed identity guards
- repeated AI tasks become automation candidates

Keep as stack-visible but not yet full Playbook runtime doctrine:

- repo-specific brand or preview verification details
- repo-specific release-ledger field choices
- Discord product-specific publication style choices

## Marker Interpretation

This package justifies:

- Core Pattern Convergence: `25%`
- Knowledge Capture & Transfer: `30%`
- Playbook Everywhere + Cortex Interface: `15%`
- AI Repetition-to-Automation Pipeline: `15%`

It also supports:

- Unified Workflow Convergence staying at `60%` with stronger doctrine spread visibility

It does not yet justify:

- Playbook runtime migration
- Cortex runtime ownership
- `_stack` automation implementation
- Discord publication automation proof
