# Stack Lane 0 Baseline Inventory

Date: 2026-05-22
Status: Active planning surface
Mode: Docs only

## Goal

Build the master truth map before convergence, cleanup, or root normalization changes the evidence.

## Lane Rule

Inventory first.

Do not:

- regenerate `stack.lock.yaml`
- switch branches for cleanup
- move raw archives
- touch product implementation code from this lane

## Convergence Placement

The strategic and operational order is now:

1. Canonical Repo Restoration
2. Tmp Dependency Elimination
3. Duplicate Surface Decommission
4. Branch & Worktree Normalization
5. Brand Asset Canonicalization
6. Preview Cache & Surface Consistency
7. Operator Secret Path Hygiene
8. Manual Deploy Exception Burn-Down
9. Fitness Supabase Profile/Data Hygiene
10. Discord OS Infrastructure Separation
11. Discord Workflow, Publication & Docs Reliability
12. Unified Workflow Convergence
13. Playbook Everywhere + Cortex Interface
14. Truth Map & ATLAS Book
15. Full Stack Re-sync, Clean & Closeout
16. Post-Convergence Lane Split Readiness

Cross-cutting doctrine lane:

- AI Long-Run Batch Orchestration remains active as a planning and contract lane, but it should not outrank canonical repo and `tmp/` restoration work.
- AI Repetition-to-Automation Pipeline remains active as a planning lane for converting repeated AI and operator asks into governed command surfaces, but it should not outrank canonical repo and `tmp/` restoration work.

## Consolidated Marker Definitions

- Vision & Future Alignment: defines the endgame, purpose, done-state, ATLAS alignment, and future-self review for the overall program.
- Canonical Repo Restoration: tracks whether canonical repo roots exist again under `repos/`, especially Fitness, and whether production workflows truly point there.
- Tmp Dependency Elimination: tracks removal of production-critical dependence on `tmp/` worktrees, deploy clones, and preservation checkouts.
- Duplicate Surface Decommission: tracks duplicate or orphaned source surfaces until each is removed, archived, retained as evidence, or routed into a canonical repo.
- Branch & Worktree Normalization: preserves and classifies branch, worktree, stash, and dirty-checkout state before cleanup or normalization.
- Brand Asset Canonicalization: tracks whether ATLAS owns the canonical branding source and downstream apps consume reproducible generated outputs.
- Preview Cache & Surface Consistency: tracks whether deployed icon, preview, PWA, and share surfaces match the canonical branding source and can be verified cleanly.
- Operator Secret Path Hygiene: tracks whether secret-backed operator flows avoid spilling env or secret residue into repo roots.
- Manual Deploy Exception Burn-Down: tracks the remaining risk from direct deploy behavior outside `_stack`.
- Fitness Supabase Profile/Data Hygiene: tracks cleanup and governance of Fitness Supabase identity/data surfaces, especially unknown, duplicate, or automation-linked profiles.
- Discord OS Infrastructure Separation: tracks extraction of Discord OS out of the Fitness-hosted default stack into its own governed repo, Vercel, Supabase, env, and contract surfaces without breaking live Discord behavior.
- Unified Workflow Convergence: makes disconnected workflows operate as one system across stack and owner repos.
- Dependency Untangling: tracks hidden coupling between lanes and reduces it so later Fitness, Discord, and ATLAS work can run in parallel safely.
- Core Pattern Convergence: tracks whether foundational reusable ideas from one lane actually spread across the stack instead of staying trapped inside a single repo, workflow, or operator habit.
- Playbook Everywhere + Cortex Interface: tracks how Playbook becomes the visible governance layer everywhere it belongs, including Cortex-facing doctrine, contracts, patterns, and validation logic.
- Knowledge Capture & Transfer: tracks whether reasoning is written into durable docs and whether a future teammate, Codex worker, or Cortex agent could continue from docs and receipts.
- Feedback Loop Readiness: tracks whether each lane can receive, process, and route user or system feedback into ATLAS, Playbook, Discord, or repo workflows.
- Sandbox Simulation Readiness: ensures each lane has safe places to test bold ideas without risking core systems.
- Truth Map & ATLAS Book: consolidates documentation, roadmaps, notes, systems, concepts, and lane maps into one definitive cross-referenced guide.
- Discord Workflow, Publication & Docs Reliability: converges Discord workflow first, stabilizes the public posting path and fallback path, then publishes the right user-facing and operator-facing docs.
- Full Stack Re-sync, Clean & Closeout: covers the whole cleanup lifecycle from normalization through verified closeout.
- Post-Convergence Lane Split Readiness: measures whether the program is ready to split safely back into Fitness, Discord, and ATLAS lanes.
- AI Repetition-to-Automation Pipeline: tracks how repeated AI, Codex, and operator tasks are identified and converted into simple governed command surfaces with verification, receipts, and rollback paths.

## Explicit Cleanup Targets Added To Existing Lanes

Do not add a separate marker for stale Vercel surface cleanup.

These targets belong under both:

- `Duplicate Surface Decommission`
- `Manual Deploy Exception Burn-Down`

Targets to review and later classify:

- `spotify-club-phase-7-interaction-reliability`
- `spotify-club-phase-7-interaction-re.vercel.app`
- `spotify-board-hygiene-main`
- `spotify-board-hygiene-main.vercel.app`

## Core Pattern Convergence Definition

This lane measures whether the strongest reusable concepts from key projects are systematically applied across the stack instead of remaining isolated inside one repo or workflow.

It starts at `0%`.

It reaches `100%` only when:

- each core repo or lane has extracted its reusable rules, patterns, and failure modes
- those patterns are mapped to where they apply across ATLAS, `_stack`, Foundation, Lifeline, Playbook, Cortex, Fitness, Discord OS, QA or LLEL, and release workflows
- Playbook records the reusable doctrine
- ATLAS docs show ownership boundaries and connection points
- implementation workflows consistently apply the shared patterns where appropriate
- old one-off local habits are replaced by governed stack-wide patterns where that spread is justified

This lane is related to but different from:

- Playbook Everywhere + Cortex Interface
  - makes governance and interpretation surfaces visible and usable
- Knowledge Capture & Transfer
  - preserves reasoning and handoff continuity
- Core Pattern Convergence
  - proves the strongest patterns actually spread into stack-wide operating practice

## Lane Questions

Every lane should answer:

- why does this exist
- what is the endgame
- what does done look like
- how does it align with ATLAS
- what should we stop doing

## Current Interpretation

- Lane 0 is no longer just a file inventory exercise.
- Lane 0 is the place where the convergence marker system becomes explicit enough to guide later cleanup.
- New strategic lanes should be recorded here before cleanup widens, so future work is measured against the durable operating model instead of short-term hygiene only.
- The reduced marker model keeps every idea but removes overlapping dashboard lines.
- The next start point is explicit: Canonical Repo Restoration plus Tmp Dependency Elimination before broader cleanup or workflow convergence.

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
