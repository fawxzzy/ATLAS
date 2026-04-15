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
- proposed session manifests live under `runtime/atlas/proposed-sessions/<session_id>/`
- session-local worker artifacts live under `runtime/atlas/sessions/<session_id>/artifacts/`
- governed tool and extension registry truth lives under `docs/registry/`

`atlas.session.v1` now has two roles:

- `governed_session`: the normal approval and execution gateway
- `proposed_session`: a non-executing next-work artifact emitted by the initiative loop

## Required Linkage

Every completed session must carry refs for:

- worker context
- worker assignment
- worker status artifacts
- capability profile
- privileged-action request
- approval receipt
- execution receipt

Every governed execution step must also carry:

- `tool_id`
- `extension_id` when the surface is extension-backed
- `registry_digest`

Conflict sessions may also carry refs for:

- merge request artifacts
- paused worker statuses
- resume-context artifacts
- resume request artifact
- resume dispatch artifact
- resumed worker assignment and status refs
- merger assignment and prompt artifacts
- supervisor merge completion artifact

## Lifecycle

1. load `stack.lock.yaml`
2. load the governed tool and extension registries from `docs/registry/`
3. create `atlas.session.v1`
4. build the Cortex worker context artifact
5. emit the worker assignment artifact
6. emit request and approval artifacts
7. invoke `_stack` to bridge into Lifeline
8. record the execution receipt and status update refs
9. if needed, run Cortex supervision and let `_stack` consume merge requests
10. if the session becomes `resume_ready`, resume only through `ops/atlas/resume_session.py`
11. close the session with an explicit final status

Proposed-session lifecycle:

1. initiative evidence and attention are clustered above sessions
2. the initiative loop emits or refreshes a `proposed_session`
3. the proposal stays queryable through awareness and status surfaces
4. no approval or execution occurs until a real governed session is created separately

## Governed Surface Rule

- `atlas.session.v1` declares the governed tool surfaces used by the session
- worker assignment, worker status, privileged-action request, approval receipt, and execution receipt artifacts must agree on `tool_id`, optional `extension_id`, and `registry_digest`
- merge-request, pause, merge, and resume artifacts must preserve the same governed surface identity instead of inventing local task names
- session state is derived from linked artifacts and receipts only

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
- `resume_failed`
- `failed`

`resume_ready` means pause, merge-request, and resume-context artifacts were emitted and the session is waiting for resumed worker execution through the existing `_stack` flow.

`resume_failed` means the root-owned resume executor dispatched or validated the resume path and failed closed.

## First Bounded Write

The first non-dry-run governed machine action is `workspace_file_apply`.

Session rule:

- the request must declare the execution `tool_id`, `registry_digest`, `stack_lock_digest`, and assignment linkage
- the write target must stay inside the declared `runtime/atlas/session-workspaces/<session_id>/` workspace root
- approval and receipt artifacts remain `approved_action`
- rollback metadata should capture the prior file hash or a backup ref when available

## Resume Lifecycle

Resume is a first-class governed session transition.

States:

- `resume_ready`
- `resume_requested`
- `running`
- `completed` or `resume_failed`

Required refs before resume:

- `refs.merge_completion_ref`
- `resume.resume_context_ref`
- resume-context `paused_handoff_refs`
- stable `stack_lock_digest`
- stable `tool_id`
- stable `registry_digest`

Resume must fail closed when merge completion is missing, the lock digest is stale, required handoff refs are missing, or governed surface identity does not match.

Voice no longer needs a bypass path because the root session layer owns the governed resume executor directly.

## Non-Goals

- no direct executor logic at the root
- no transcript scraping for lifecycle inference
- no second orchestration model beside `_stack` worker artifacts and Lifeline receipts
- no proposal artifact that silently becomes execution state
