# Cortex Stack Advisory Handoff

- Generated: `2026-06-05T08:33:37.093359+00:00`
- Handoff id: `stack-advisory-handoff-stabilize-root-worktree`
- Authority level: `read_only_advisory`
- Consumer: `_stack`
- Consumption mode: `artifact_refs_only`
- Next recommended lane: `stabilize-root-worktree` (atlas)
- Handoff status: `ready`
- Ready for _stack consumer: `yes`
- Routing mode: `explicit_artifact_ref_handoff`
- Automatic dispatch: `no`
- Execution authorized: `no`
- Receipt authorized: `no`

## Handoff Checks
- `worker-prompt-contract-version`: passed - Worker prompt uses the promoted Cortex worker-prompt contract.
- `worker-prompt-authority-read-only`: passed - Worker prompt remains read-only advisory.
- `consumer-is-stack-advisory`: passed - Canonical handoff targets _stack as an advisory artifact consumer only.
- `routing-contract-promoted`: passed - Canonical handoff promotes an explicit artifact-ref routing contract.
- `no-automatic-dispatch-or-authority`: passed - Canonical handoff does not enable automatic dispatch, execution, receipt authority, owner-truth mutation, or transcript scraping.
- `context-packet-matches-lane`: passed - Context packet is explicitly linked to the selected lane.
- `operator-surface-lane-matches-worker-prompt`: passed - Operator surface and worker prompt agree on the next lane.
- `ledger-lane-matches-worker-prompt`: passed - Ledger and worker prompt agree on the next lane.
- `transcript-scraping-absent`: passed - Canonical handoff consumes explicit artifact refs only and does not scrape transcripts.
- `separated-surfaces-preserved`: passed - Planner, context, proof, receipt-draft, and final receipt stay separately referenceable.

## Authority Guards
- Canonical handoff is advisory only and does not dispatch _stack work.
- Default routing promotion means explicit artifact-ref handoff shape only; automatic dispatch remains disabled.
- Cortex does not grant execution, owner-truth mutation, or Lifeline final receipt authority through the handoff.
- Transcript scraping remains disallowed; planner, context, proof, receipt-draft, and final receipt stay separately referenceable.

## Source Refs
- `runtime/cortex/worker-prompts/latest.json`
- `runtime/cortex/context/latest.json`
- `runtime/cortex/operator-surface/latest.json`
- `runtime/cortex/ledger/latest.json`
- `runtime/cortex/kernel.state-model.seed.v1.json`
- `runtime/cortex/kernel.rule-registry.seed.v1.json`
- `runtime/cortex/current-state/latest.json`
- `runtime/cortex/rail-state/latest.json`
- `runtime/receipts/validation/stack-validation.latest.json`
- `runtime/cortex/kernel.proof-summary.examples.v1.json`
- `stack.lock.yaml`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/memory/profiles/zachariah_workflow_profile.json`
- `runtime/cortex/worker-prompts/latest.json#/planner_contract`
- `runtime/cortex/worker-prompts/latest.json#/receipt_draft_preview`
