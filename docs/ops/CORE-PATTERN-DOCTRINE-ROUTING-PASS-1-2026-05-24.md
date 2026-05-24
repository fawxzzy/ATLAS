# Core Pattern Doctrine Routing Pass 1

Date: 2026-05-24
Lane: Core Pattern Convergence
Mode: docs-only doctrine routing pass
Status: first admission routing baseline recorded

## Goal

Decide which current core-pattern entries are ready for Playbook-owned doctrine, which should remain ATLAS-only operating notes, which should feed future `_stack` automation, which Cortex may read as planning context, and which should remain deferred until more proof exists.

This pass does not migrate Cortex runtime ownership, change Playbook runtime behavior, implement `_stack` commands, or mutate repo runtime surfaces.

## Routing Labels

Playbook admission status used in this pass:

- `admit now`
- `defer`
- `ATLAS-only`
- `_stack automation candidate`
- `Cortex planning candidate`

Interpretation rule:

- one pattern may route to more than one future surface
- the admission status names the strongest current next action
- `admit now` means wording is stable enough for Playbook-owned reusable governance
- `_stack automation candidate` means the pattern is already useful but the next real value is operator-surface implementation, not more doctrine wording
- `Cortex planning candidate` means Cortex may consume the pattern as planning context without becoming runtime owner

## Admission Threshold For This Pass

Promote to Playbook now only if all are true:

1. the pattern is already evidenced by receipts, checkpoints, or repeat cross-lane use
2. the wording is stable enough to be reusable outside the origin lane
3. the owner boundary is clear
4. promoting now reduces operator confusion more than it increases doctrine noise

Keep as ATLAS-only if any are true:

- the pattern is still stack-program framing more than reusable governance
- the rule is still too repo-specific
- the lesson is visible and useful, but not yet stable enough for doctrine promotion

Route to `_stack` automation candidate if any are true:

- the behavioral truth is already clear
- the main remaining value is mechanical enforcement or command implementation
- there is an obvious shared operator seam

Expose to Cortex planning if any are true:

- the pattern helps admission, sequencing, prioritization, or risk framing
- runtime ownership is not required for Cortex to benefit

## Routing Matrix

| Pattern name | Current evidence | Proposed owner | Playbook admission status | Required verification | Non-goals |
| --- | --- | --- | --- | --- | --- |
| owner repo truth over `tmp` or worktree truth | canonical repo restoration receipts, tmp elimination receipts, root routing doctrine, stack lock alignment | Playbook for reusable rule, ATLAS for stack projection, `_stack` later for enforcement | admit now | continued reuse outside Fitness plus lock-truth preservation in future repo lanes | not a mandate to eliminate every temporary workspace; not runtime migration |
| preserve or classify before delete | archive normalization, duplicate surface decommission, retention routing receipts | Playbook for reusable cleanup doctrine, ATLAS for retention decisions | admit now | future residue or branch cleanup lane should reuse the same preservation-before-disposal shape | not blanket refusal to delete; not backup-policy redesign |
| one owner seam before execution | operator ladder, branch and worktree normalization, root routing doctrine | Playbook for governance wording, ATLAS for program routing, `_stack` later for command enforcement | admit now | future multi-repo or multi-agent lane should declare owner surface up front and preserve that in receipts | not a ban on cross-repo work; not a branch-per-file rule |
| no Discord post before proof | unified release handoff, unified QA proof handoff, Discord OS workflow boundary, publication corrections | Playbook for reusable publication rule, Discord OS for product-specific execution | admit now | later Discord publication automation should prove the rule is machine-checkable | not a ban on internal draft copy; not a requirement that all proof be automated |
| no manual deploy by default | manual deploy exception inventory, decision pass, burn-down checkpoint, Fitness clarification | Playbook for deploy-governance doctrine, `_stack` for eventual enforcement | admit now | Trove and Mazer residual documentation should preserve the same authority split | not a ban on explicitly approved recovery deploys; not Vercel policy mutation by itself |
| `_stack` owns deploy authority | deploy handoff map, Fitness authority clarification, Trove and Mazer preflights, burn-down checkpoint | Playbook for rule wording, `_stack` for runtime enforcement | admit now | future app onboarding should prove preview and prod authority stays in `_stack` | not a claim that `_stack` owns all runtime logic; not repo-local release prep removal |
| repo-local commands prepare and verify, not deploy | Fitness release-script authority clarification, operator ladder, deploy checkpoint | Playbook for reusable repo/deploy split, owner repos for local docs | admit now | Trove and Mazer docs should eventually mirror the same distinction if local release helpers widen | not a ban on local build or release notes; not removal of all repo scripts |
| receipt-backed closeout | convergence maps, stack-lock decisions, QA receipts, release receipts, closeout checkpoints | Playbook for reusable closeout doctrine, ATLAS for root packaging | admit now | later automation lanes should prove receipts can be packaged consistently without weakening signal | not a requirement that every tiny local note becomes a receipt; not replacement for repo-local changelogs |
| fail-closed identity guards | Trove and Mazer deploy identity hardening, Fitness deploy posture, preflight proofs | Playbook for rule wording, `_stack` for technical enforcement | admit now | at least one more non-Vercel or non-deploy identity seam should reuse the same pattern | not secret rotation policy; not broad connector migration |
| canonical source -> generated outputs -> consumer sync | brand asset canon, launcher icon proof, preview/cache planning, hash receipts | ATLAS for stack pattern framing now, Playbook later if reuse broadens | ATLAS-only | remote preview and unfurl verification lane plus at least one additional consumer domain should reuse the same source-to-consumer chain | not a mandate that every generated artifact becomes root-owned; not design-system implementation |
| no `tmp` fallback for source truth | canonical repo restoration, brand lanes, QA proof maps, explicit no-tmp confirmations | Playbook for source-truth rule, ATLAS for stack posture projection | admit now | future release packaging or recovery docs should keep proving this stays true | not a ban on temporary captures or scratch runtime state; not deletion of all `tmp` usage |
| clean worktree before lane execution | branch and worktree normalization, operator ladder, root branch discipline notes | Playbook for reusable preflight rule, `_stack` later for enforcement | admit now | future parallel lanes or automation pilots should prove clean-surface checks happen before apply | not a requirement that every repo be globally pristine before all work; not destructive cleanup authority |
| branch name is metadata, diff and ownership are truth | branch normalization receipts, root branch-discipline notes, recovery packaging | Playbook for failure-mode wording, Cortex for planning caution | admit now | future parallel or recovery lanes should keep classifying ownership by diff and surface, not branch label alone | not anti-branch doctrine; not a claim branch names are useless |
| repeated AI tasks become automation candidates | operator ladder, playbook handoff, repetition-to-automation doctrine in notes, repeated publication and packaging asks | Playbook for behavioral doctrine, `_stack` and Discord OS for later command surfaces, Cortex for prioritization | admit now | at least one repeated workflow should graduate into a governed command with verification and rollback | not automation of unstable workflows; not unattended mutation by default |
| verify -> plan -> apply -> verify | Playbook notes, origin research trail, convergence maps, existing remediation framing | Playbook primary owner | admit now | continue using the sequence in future operator and proof lanes without compressing plan/apply boundaries | not a rigid mandate that every tiny edit requires a heavyweight plan receipt |
| local proof before release or public update | QA/LLEL handoff, release handoff, update rules, Fitness proof lanes | Playbook for reusable readiness doctrine, QA/LLEL for proof execution | admit now | at least one additional repo beyond Fitness should preserve the same proof-before-release shape | not a requirement that all proof classes are identical; not public-update automation yet |
| feedback or update lessons become doctrine only after bounded evidence | Discord OS boundary, card detail corrections, publication cleanup, handoff map | Playbook for doctrine-admission rule, ATLAS for evidence routing, Cortex for planning awareness | admit now | future Discord workflow extraction review should prove lessons are promoted from bounded evidence rather than chat-only sentiment | not a ban on fast operational fixes; not a requirement that every lesson becomes doctrine |

## Pattern Routing Notes

### Admit Into Playbook Now

These patterns are ready for Playbook-owned reusable doctrine now because they already have repeat evidence, stable wording, and clear cross-lane value:

- owner repo truth over `tmp` or worktree truth
- preserve or classify before delete
- one owner seam before execution
- no Discord post before proof
- no manual deploy by default
- `_stack` owns deploy authority
- repo-local commands prepare and verify, not deploy
- receipt-backed closeout
- fail-closed identity guards
- no `tmp` fallback for source truth
- clean worktree before lane execution
- branch name is metadata, diff and ownership are truth
- repeated AI tasks become automation candidates
- verify -> plan -> apply -> verify
- local proof before release or public update
- feedback or update lessons become doctrine only after bounded evidence

These are strong enough because they are no longer just Fitness-specific or one-lane observations. They now shape deploy, proof, publication, cleanup, and routing behavior across the stack.

### Keep ATLAS-Only For Now

Keep this pattern ATLAS-only for now:

- canonical source -> generated outputs -> consumer sync

Reason:

- the pattern is clearly real and useful
- current proof is still concentrated in brand, icon, and preview/cache work
- the reusable wording is not yet broad enough to treat it like a general Playbook contract across all repos and product surfaces

Next proof needed before Playbook promotion:

- remote preview and unfurl verification closeout
- at least one additional non-brand consumer chain using the same source -> generated -> consumer pattern

### Route To `_stack` Automation Later

These entries are already doctrine-worthy, but the next practical value is enforcement or operator-surface implementation:

- one owner seam before execution
- no manual deploy by default
- `_stack` owns deploy authority
- receipt-backed closeout
- fail-closed identity guards
- clean worktree before lane execution
- repeated AI tasks become automation candidates

Reason:

- these patterns already have stable governance wording
- repeating more prose alone will not reduce operator burden much further
- the next leverage is shared command or preflight implementation

### Expose To Cortex As Planning Context

Cortex may consume all `admit now` patterns as planning context, with especially high value on:

- owner repo truth over `tmp`
- one owner seam before execution
- branch name is metadata, diff and ownership are truth
- repeated AI tasks become automation candidates
- feedback or update lessons become doctrine only after bounded evidence
- verify -> plan -> apply -> verify

Reason:

- these directly improve sequencing, lane admission, workload routing, and evidence interpretation
- Cortex can use them without owning runtime or promoting doctrine automatically

## Deferred Or Parked Areas

No current matrix entry is fully parked as `defer` in this pass. The matrix already filtered for strong cross-lane candidates, and every listed entry is useful now either as Playbook doctrine, ATLAS-only operating pattern, `_stack` automation candidate, or Cortex planning context.

The closest thing to a defer posture is:

- `canonical source -> generated outputs -> consumer sync`

It is not deferred from visibility. It is deferred only from Playbook doctrine admission until the proof surface broadens.

## Required Verification Before The Next Routing Pass

Before a future doctrine routing pass moves more entries into stronger automation or broader doctrine claims, the stack should gather:

1. one additional repo or service proving `local proof before release or public update`
2. one additional identity seam proving `fail-closed identity guards` outside the current Trove and Mazer deploy wrappers
3. one additional source-consumer lane proving `canonical source -> generated outputs -> consumer sync` beyond current brand and preview work
4. one real graduated operator surface proving `repeated AI tasks become automation candidates` has turned into a governed command
5. one Discord extraction review proving bounded evidence promotion remains enforced

## Non-Goals

This routing pass does not:

- edit Playbook runtime or contract files
- create `_stack` commands
- migrate Cortex into runtime ownership
- change repo-local docs outside ATLAS root
- reopen paused deploy-backed preview verification
- broaden the current matrix with speculative low-evidence patterns

## Recommendation

The next doctrine move should still be planning, not implementation:

1. admit the `admit now` set into Playbook-owned governance wording in a later dedicated promotion pass
2. keep `canonical source -> generated outputs -> consumer sync` as ATLAS-only until the proof surface widens
3. choose one narrow automation candidate after doctrine promotion, likely:
   - receipt-backed closeout
   - repeated updates/release packaging
   - clean-worktree or owner-seam preflight checks

## Marker Interpretation

This package justifies:

- Core Pattern Convergence: `35%`
- Playbook Everywhere + Cortex Interface: `20%`
- Knowledge Capture & Transfer: `35%`
- AI Repetition-to-Automation Pipeline: `20%`

It supports Unified Workflow Convergence remaining at `60%`.

It does not yet justify:

- Playbook runtime implementation
- Cortex runtime migration
- `_stack` automation rollout
- Discord publication automation proof
