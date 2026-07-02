# AI Work Session Stability Auto-Sync Loop Read-Only Closeout Aggregator First-Implementation Admission

- CODEX-MSG-ID: `CODEX-2026-07-02-AI-WORK-SESSION-STABILITY-POST-OWNER-LANE-SEPARATION-NEXT-SLICE-SELECTION`
- Date: `2026-07-02`
- Mode: `docs-only first-implementation admission`
- Scope: `admit a future read-only AI work-session closeout aggregator, define its contract, and preserve no-mutation boundaries before worker implementation`
- Branch basis: `main@e33b03dc`
- Worker implementation: `not included`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Admission Decision

Admit a future first implementation for:

- `ops/atlas/ai_work_session_closeout.py`
- `tests/test_atlas_ai_work_session_closeout.py`

This receipt does not create those files. It only admits the next prompt-pack / worker handoff contract.

## Why This Slice Exists

The preflight helper answers whether a session is safe to begin or continue. The missing paired surface is a read-only closeout helper that answers whether a session is safe to stop, what changed, what remains blocked, what validation evidence exists, and what the next exact action should be.

The repeated stall pattern came from treating closeout as narrative memory instead of a structured receipt. A closeout aggregator gives later projection freshness, Playbook/Cortex utilization, and repetition-to-automation packets a consistent input shape.

## Future Worker Contract

The future worker must default to read-only inspection and emit a structured closeout payload. It may read root state, Git state, marker selector output, continuity health, validation receipts, and known protected-surface paths. It must not mutate owner repos, platform state, secrets, deploy surfaces, or protected runtime/archive surfaces.

Required output fields:

```json
{
  "schema_version": "atlas.ai_work_session_closeout.v1",
  "status": "ok | advisory_drift | blocker | internal_error",
  "generated_at": "ISO-8601 UTC timestamp",
  "branch": "current branch",
  "head": "current commit",
  "parity": {
    "upstream": "upstream ref",
    "ahead": 0,
    "behind": 0
  },
  "changes": {
    "working_tree": [],
    "staged": [],
    "committed": [],
    "pushed": false
  },
  "touched_repos": [],
  "commands": [],
  "validation": {
    "stack_validation": null,
    "tests": []
  },
  "markers": {
    "changed": [],
    "current_board": []
  },
  "blockers": [],
  "warnings": [],
  "local_residue": [],
  "protected_surfaces": {
    "touched": [],
    "blocked": []
  },
  "owner_repo_scope": "none | read_only | mutation_requested",
  "platform_scope": "none | read_only | mutation_requested",
  "safe_to_close": false,
  "required_followups": [],
  "next_action": null
}
```

Required status semantics:

- `ok`: no blocking residue, validation is sufficient for the claimed scope, and the exact next action is known.
- `advisory_drift`: non-blocking drift exists and is reported without claiming readiness beyond evidence.
- `blocker`: the lane cannot honestly proceed without new access, proof, owner-repo work, platform action, or user approval.
- `internal_error`: the helper could not inspect required local state.

## Proof Matrix For Future Worker

The next worker packet must prove:

- direct unit coverage for clean closeout, dirty tree, blocked proof, and protected-surface cases
- no mutation unless an explicit future flag is admitted
- stable JSON output
- human-readable summary output
- correct treatment of owner-repo dirt as advisory or blocking according to `stack.yaml` / inventory truth
- correct marker no-movement behavior when no receipt-backed threshold is met

## Marker Decision

No marker moves from this admission packet.

`AI Work Session Stability & Auto-Sync Loop` remains `25%`.

A future ratchet above `25%` requires the closeout worker and tests to land, plus a reconciliation receipt proving the helper was used without widening into owner/platform/protected mutation.

## Next Packet

`AI Work Session Stability & Auto-Sync Loop read-only closeout aggregator prompt-pack and worker handoff contract`

That next packet should freeze exact worker touch surfaces, command shape, test cases, allowed outputs, stop conditions, and the final worker-cluster reconciliation package.
