# Stack Lane 0 Truth Map

Date: 2026-05-22
Status: Active planning surface
Mode: Docs only

## Purpose

Record the lane map and consolidated marker definitions that the convergence program should use before cleanup and implementation continue.

## Core Reading

The convergence program is no longer just:

- inventory
- converge
- clean

It now also includes explicit strategic lanes that make the operating model durable enough to survive handoff, batching, and future lane splits.

## Strategic Lane Map

| Lane | Why it exists | Endgame |
| --- | --- | --- |
| Vision & Future Alignment | prevent local optimization against the wrong target and periodically check long-term fit | every lane has a stated purpose, done-state, ATLAS alignment, and future-self review |
| Inventory & Truth Map | identify current truth before changes widen | one reliable map of owner truth, projections, duplicates, and unknowns |
| Canonical Repo Restoration | restore canonical repo truth under `repos/` and remove ambiguity about the real production roots | production workflows point at the real canonical repos instead of temporary surfaces |
| Tmp Dependency Elimination | remove production-critical dependence on `tmp/` worktrees and deploy clones | `tmp/` is no longer a hidden source-of-truth or deploy surface |
| Duplicate Surface Decommission | classify and retire duplicate or orphaned source surfaces | no hidden parallel source roots remain outside canonical repos or documented evidence |
| Branch & Worktree Normalization | preserve and classify active branch state before cleanup | no meaningful work is lost while returning to intentional baselines |
| Brand Asset Canonicalization | make ATLAS the single governed branding source | app icons, OG images, favicons, launcher art, and Trove assets derive from one reproducible source |
| Preview Cache & Surface Consistency | verify that deployed preview surfaces match the canonical branding source | icon and preview drift is either absent or classifiable as cache-only with a documented verification path |
| Operator Secret Path Hygiene | keep secret-backed operator flows from polluting repo roots | temporary env pulls and secret-backed operations leave no ambiguous residue |
| Manual Deploy Exception Burn-Down | remove direct deploy ambiguity outside `_stack` | deploy truth is singular, reproducible, and operator-readable |
| Fitness Supabase Profile/Data Hygiene | classify and govern Fitness identity/data cleanup before mutation | auth/profile/data truth is inventoried, cleanup is reviewable, and canonical profile usage is explicit |
| Local Data Gateway | make local preprocessing the default boundary before data leaves the machine or repo | raw inputs become minimal schema-aware packets with provenance, sensitivity labeling, and transformation history before remote refinement or sync |
| Unified Workflow Convergence | reduce duplicated release and operating paths across stack and repos | one coherent operating model across the whole system |
| Dependency Untangling | reduce hidden coupling between lanes | future Fitness, Discord, and ATLAS lanes can move in parallel safely |
| Core Pattern Convergence | spread the strongest reusable concepts across the stack instead of leaving them trapped inside one repo or workflow | reusable rules, patterns, and failure modes from core lanes are mapped, owned, visible, and actually applied across stack systems |
| Playbook Everywhere + Cortex Interface | align doctrine, verification surfaces, and Cortex-facing interpretation under one governance layer | Playbook becomes the readable interface for shared workflow and Cortex contract logic |
| Knowledge Capture & Transfer | stop losing key reasoning in chat and make future continuation possible | rules, patterns, failures, decisions, and handoff context are durable |
| Feedback Loop Readiness | route feedback back into the right system | user and system feedback are captured and assigned cleanly |
| Sandbox Simulation Readiness | test bold ideas safely | experimental work happens in protected lanes, not on core surfaces |
| AI Long-Run Batch Orchestration | define the future supervised batching architecture clearly before implementation | bounded jobs, isolated worktrees, checkpoints, and verification gates become the approved long-run model |
| AI Repetition-to-Automation Pipeline | convert repeated AI and operator asks into governed command surfaces before they waste more context and tokens | repeated safe workflows are detected, classified, and routed into `_stack`, Playbook, or bot commands with receipts and rollback paths |
| Truth Map & ATLAS Book | consolidate the cross-referenced guide | one definitive guide to systems, lanes, concepts, and maps |
| Discord OS Infrastructure Separation | extract Discord OS from the Fitness-hosted default stack into explicit repo, Vercel, Supabase, env, and contract surfaces | Discord OS runs on governed standalone infrastructure without hidden Fitness coupling or broken live behavior |
| Discord Workflow, Publication & Docs Reliability | converge Discord workflow, stabilize `#updates` publication, and publish the right durable summaries | Discord workflow, public posting, fallback path, and docs publication become one stable operator surface |
| Full Stack Re-sync, Clean & Closeout | close the normalization program honestly from re-sync through closeout | root and repos return to intentional, auditable baselines |
| Post-Convergence Lane Split Readiness | measure readiness to split the system back into product lanes | Fitness, Discord, and ATLAS can run as distinct lanes safely after convergence |

## Lane Questions

Every lane should answer:

- why does this exist
- what is the endgame
- what does done look like
- how does it align with ATLAS
- what should we stop doing

## Program Interpretation

- Vision & Future Alignment belongs near the front because later cleanup without a stable endgame can optimize the wrong system.
- Canonical Repo Restoration and Tmp Dependency Elimination now belong before broader convergence because the stack cannot safely converge workflows while production truth still depends on `tmp/` or missing canonical repo roots.
- Branch & Worktree Normalization belongs before broad re-sync because the current root still contains intentional preservation residue.
- Fitness Supabase Profile/Data Hygiene belongs after secret-path inventory because identity/data cleanup should not start until operator secret handling is mapped.
- Local Data Gateway belongs beside secret-path and data-hygiene lanes because the governing question is not only where secrets live, but whether raw data is refined locally before export.
- Discord OS Infrastructure Separation supersedes the older extraction-review framing because the real issue is infrastructure ownership and hidden coupling, not just doctrine classification.
- AI Long-Run Batch Orchestration belongs as doctrine and planning now, with later implementation routed through `_stack`, Playbook, and explicit lane contracts.
- AI Repetition-to-Automation Pipeline belongs alongside `_stack` readiness and AI batching, but stays distinct: batching governs long jobs, while this lane governs noticing repetition and converting it into commands.
- Core Pattern Convergence belongs beside doctrine and knowledge lanes, but stays distinct: capture preserves ideas, interface makes them visible, and convergence measures whether the best ideas actually spread into shared operating practice.
- Knowledge Capture & Transfer is first-class because durable operations require reasoning to survive beyond one chat session.
- The reduced marker model should be used going forward so progress reporting stays durable and readable.

## Explicit Existing-Lane Cleanup Targets

Stale Vercel surface cleanup does not get its own marker.

It is an explicit target set under:

- `Duplicate Surface Decommission`
- `Manual Deploy Exception Burn-Down`

Current targets to inventory and later classify:

- `spotify-club-phase-7-interaction-reliability`
- `spotify-club-phase-7-interaction-re.vercel.app`
- `spotify-board-hygiene-main`
- `spotify-board-hygiene-main.vercel.app`

## Lockfile Deferral

Lane 0 must preserve the current lockfile deferral doctrine:

- do not regenerate `stack.lock.yaml` yet
- do not treat current lock drift as the normalization target
- regenerate the lock only after preservation classification and root reconciliation

## Marker Table

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
- Canonical Repo Restoration: `0%`
- Tmp Dependency Elimination: `0%`
- Duplicate Surface Decommission: `0%`
- Branch & Worktree Normalization: `92%`
- Brand Asset Canonicalization: `0%`
- Preview Cache & Surface Consistency: `0%`
- Operator Secret Path Hygiene: `10%`
- Manual Deploy Exception Burn-Down: `65%`
- Fitness Supabase Profile/Data Hygiene: `0%`
- Local Data Gateway: `0%`
- Unified Workflow Convergence: `60%`
- Inventory & Truth Map: `20%`
- Full Stack Re-sync, Clean & Closeout: `22% paused`
- Vision & Future Alignment: `0%`
- Dependency Untangling: `0%`
- Core Pattern Convergence: `35%`
- Playbook Everywhere + Cortex Interface: `20%`
- Knowledge Capture & Transfer: `35%`
- Feedback Loop Readiness: `20%`
- Sandbox Simulation Readiness: `0%`
- AI Long-Run Batch Orchestration: `20%`
- AI Repetition-to-Automation Pipeline: `20%`
- Truth Map & ATLAS Book: `0%`
- Discord OS Infrastructure Separation: `0%`
- Discord Workflow, Publication & Docs Reliability: `10%`
- Post-Convergence Lane Split Readiness: `0%`
