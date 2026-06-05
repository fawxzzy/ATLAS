# ATLAS Book

The ATLAS Book is the durable truth-map spine for the stack.

It exists to cross-reference:

- current stack state
- lane and marker posture
- operating model and owner boundaries
- approval-gated mutation lanes and recently closed mutation chains
- major receipts worth preserving beyond one repo

This surface is docs-only.

It does not replace:

- owner-repo runtime truth
- repo-local release ledgers
- Discord operational state
- Playbook governance ownership
- `_stack` operator execution ownership

Start here:

- [Index](INDEX.md)
- [Current State](01-current-state.md)
- [Lanes And Markers](02-lanes-and-markers.md)
- [Operating Model](03-operating-model.md)
- [Approval Gates](04-approval-gates.md)
- [Receipt Index](05-receipt-index.md)
- [System Ownership](06-system-ownership.md)
- [Contracts And Seams](07-contracts-and-seams.md)
- [Workflow Recipes](08-workflow-recipes.md)
- [Automation And Command Candidates](09-automation-and-command-candidates.md)
- [Failure Modes And Recovery](10-failure-modes-and-recovery.md)
- [Current System Map / Graph](11-system-map-graph.md)
- [Restart And Handoff Guide](12-restart-and-handoff-guide.md)
- [Vision And Endgames](13-vision-and-endgames.md)
- [Lane Split Execution](14-lane-split-execution.md)
- [Lifeline](15-lifeline.md)

This chapter set now covers:

- what the stack is
- who owns which surfaces
- how common workflows should run
- which repeated work is safe to automate later
- how common failures should be prevented and recovered
- how the current repos, runtimes, data systems, and approvals connect
- how to restart the stack from a new chat without reconstruction
- what each major lane is actually trying to finish
- how each future lane should safely reopen
- how the current closeout ladder is reducing branch, tmp, Vercel, and residue drift without reopening runtime mutation
