# ATLAS Book Index

## Purpose

The ATLAS Book is the first durable truth-map structure for the stack after the current convergence work.

It is meant to answer:

- what the stack currently looks like
- which lanes are active, paused, or approval-gated
- which surface owns what
- how work should flow between Fitness, Discord, `_stack`, Playbook, and ATLAS
- where the important receipts live

## Sections

1. [Current State](01-current-state.md)
2. [Lanes And Markers](02-lanes-and-markers.md)
3. [Operating Model](03-operating-model.md)
4. [Approval Gates](04-approval-gates.md)
5. [Receipt Index](05-receipt-index.md)
6. [System Ownership](06-system-ownership.md)
7. [Contracts And Seams](07-contracts-and-seams.md)
8. [Workflow Recipes](08-workflow-recipes.md)
9. [Automation And Command Candidates](09-automation-and-command-candidates.md)
10. [Failure Modes And Recovery](10-failure-modes-and-recovery.md)
11. [Current System Map / Graph](11-system-map-graph.md)
12. [Restart And Handoff Guide](12-restart-and-handoff-guide.md)
13. [Vision And Endgames](13-vision-and-endgames.md)
14. [Lane Split Execution](14-lane-split-execution.md)
15. [Lifeline](15-lifeline.md)
16. [Runtime Placement](16-runtime-placement.md)
17. [Creation OS Target Architecture](17-creation-os-target-architecture.md)

## Current Emphasis

This seed structure reflects:

- docs-first convergence
- explicit approval gates before mutation
- the Fitness / Discord / ATLAS lane split model
- DiscordOS separation planning without implementation
- Fitness Supabase profile/data hygiene closed at `100%` with Discord and Music Sesh boundaries transferred to DiscordOS separation

The next expansion layer captures:

- ownership by system
- cross-system contracts and seams
- approval-gated boundaries that must not be bypassed

The current expansion layer also adds:

- reusable workflow recipes
- allowed owner surfaces
- proof, receipt, and approval expectations by workflow

The next expansion layer adds:

- repeated operator tasks worth tracking
- candidate `_stack`, Playbook, and Discord command surfaces
- automation boundaries that should remain human-reviewed or approval-gated

The current expansion layer now also adds:

- first safe automation candidates
- explicit "never automate directly" rules
- linkage from repeated work to the AI automation lanes

The next expansion layer now adds:

- common stack failure modes
- bounded recovery playbooks
- lane and receipt ownership for recovery work

The current expansion layer now also adds:

- a cross-system map for repos, runtime, Supabase, Vercel, and approvals
- a machine-readable appendix for lane status, blockers, and next packages

The current expansion layer also now adds:

- a restart path for new chats
- exact approval phrases and handoff format
- current recommended next packages

The current expansion layer now also adds:

- lane endgames
- blocker-aware future alignment
- a shared test for when the split is actually working

The current expansion layer now also adds:

- lane reopen checklists
- blocker and receipt expectations by lane
- first safe package guidance for actual split execution

The current closeout layer now also adds:

- green normal-validation confirmation after stack and registry repair
- bounded classification for branch/worktree, tmp, helper Vercel, and Fitness residue pressure
- a narrow next-package ladder toward 100 instead of another broad convergence pass

The current target-architecture layer now also adds:

- a human-directed Creation OS product definition and software-builder wedge
- deterministic builder and conversational creative loop separation
- a backend-neutral bootstrap pointer and memory-tier contract
- unmeasured staged roadmap candidates without changing marker percentages
