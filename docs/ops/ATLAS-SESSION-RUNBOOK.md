# ATLAS Session Runbook

`atlas.session.v1` is the root-owned manifest for one governed ATLAS task. It is the session truth surface for root orchestration.

## Scope

- root sessions coordinate existing `_stack`, Cortex, and Lifeline artifacts
- root sessions do not execute work directly
- root sessions do not replace `_stack` worker contracts
- session state comes from manifests and receipts, not terminal logs

## Session Artifact Lane

- session manifests live under `runtime/atlas/sessions/<session_id>/`
- the canonical manifest path is `runtime/atlas/sessions/<session_id>/session.manifest.json`
- session-local worker artifacts live under `runtime/atlas/sessions/<session_id>/artifacts/`

## Required Linkage

Every completed session must carry refs for:

- worker context
- worker assignment
- worker status artifacts
- capability profile
- privileged-action request
- approval receipt
- execution receipt

Conflict sessions may also carry refs for:

- merge request artifacts
- paused worker statuses
- resume-context artifacts
- merger assignment and prompt artifacts
- supervisor merge completion artifact

## Lifecycle

1. load `stack.lock.yaml`
2. create `atlas.session.v1`
3. build the Cortex worker context artifact
4. emit the worker assignment artifact
5. emit request and approval artifacts
6. invoke `_stack` to bridge into Lifeline
7. record the execution receipt and status update refs
8. if needed, run Cortex supervision and let `_stack` consume merge requests
9. close the session with an explicit final status

## Commands

Read-only end-to-end session:

```powershell
python .\ops\atlas\run_session.py --task-id atlas-session-readonly --query-term "atlas interoperability"
```

Conflict fixture session:

```powershell
python .\ops\atlas\run_session.py --task-id atlas-session-conflict --scenario conflict --query-term "atlas session"
```

## Final Status Rule

The session manifest closes with one explicit `completion.final_status`.

Current final statuses:

- `completed`
- `resume_ready`
- `failed`

`resume_ready` means pause, merge-request, and resume-context artifacts were emitted and the session is waiting for resumed worker execution through the existing `_stack` flow.

## Non-Goals

- no direct executor logic at the root
- no transcript scraping for lifecycle inference
- no second orchestration model beside `_stack` worker artifacts and Lifeline receipts
