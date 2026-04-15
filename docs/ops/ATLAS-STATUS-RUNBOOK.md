# ATLAS Status Runbook

The ATLAS status view is rendered from artifact descriptors only.

## Contract

- status reads `runtime/cortex/artifacts/**`
- status reads the governed registry snapshot from `docs/registry/`
- status does not inspect raw session logs
- status does not infer worker completion from terminal output

## Questions Answered

The current status read model answers:

- what session is active
- what descriptors exist
- which governed tool and extension surfaces are registered
- which workers are blocked or paused
- which merge requests are still open
- which merge-request artifacts are retained residue rather than current live truth
- which receipts closed the selected session
- which quarantined trust surfaces remain metadata-only or untrusted
- which current anomalies require operator review before more work is launched
- which sessions are mid-resume or failed-resume
- which initiatives are active, which ones still carry open attention, which ones already have proposed next sessions, and which ones are linked to repo work
- which conversations are active and which recent conversation turns requested governed follow-up

## Command

Render the global view:

```powershell
python .\ops\cortex\render_status.py
```

Render one session:

```powershell
python .\ops\cortex\render_status.py --session-id <session_id>
```

Build the world-model artifacts first:

```powershell
python .\ops\cortex\build_world_model.py
```

## Governed Surface View

The status renderer exposes governed surface identity from descriptors only:

- session manifests declare the session's governed surfaces
- worker descriptors expose `tool_id`, optional `extension_id`, and `registry_digest`
- receipt descriptors expose the same governed identity for the closing execution step
- receipt supersession is resolved from descriptors, so the preferred closing receipt may differ from the original historical receipt ref
- the top-level registry section reports the current registry digest and entry counts

## Receipt Supersession Rule

When a truthful repaired execution receipt exists, status prefers the superseding receipt for current-state reads while keeping the original receipt visible.

Current status output exposes this through:

- `active_session.execution_receipt_ref`
- `active_session.original_execution_receipt_ref`
- `closure_receipts[*].source_ref`
- `closure_receipts[*].original_source_ref`
- `closure_receipts[*].supersedes_receipt_ref`
- `closure_receipts[*].reconciled_at`
- `closure_receipts[*].reconciled_by_tool_version`
- `closure_receipts[*].repair_basis_refs`

## Attention Queue

The status payload also emits an `attention_queue` read model.

This is a derived operator surface, not an execution queue.

Current attention items may include:

- registry load failure
- registry drift between the active session and the current registry bundle
- historical sessions in `legacy_pre_registry` compatibility mode
- unknown governed tool or extension ids referenced by active artifacts
- blocked or paused workers
- open merge requests
- failed or missing closure receipts
- active sessions waiting in `resume_ready`
- root-owned resume failures
- untrusted knowledge surfaces that remain quarantined
- conversation turns that requested governed follow-up
- initiative-owned repo work that is waiting on a governed soak, blessing, or manual review decision

The queue must stay descriptor-backed and deterministic. It must not inspect transcripts, terminal output, or raw imported evidence.

## Epoch Compatibility

Governed runtime history is epoch-aware.

The registry-backed governed epoch starts at **2026-04-14T08:06:53Z**.

Status behavior by epoch:

- `governed_v1` surfaces missing `tool_id`, `registry_digest`, observation-chain, or closure evidence as blocking governance defects
- `legacy_pre_registry` surfaces those same gaps through descriptor-backed compatibility records instead of pretending the old artifact was minted under the new contract

Current status output exposes legacy compatibility through:

- `legacy_compatibility`
- `runtime/state/atlas/legacy-backfill/*.json`
- `runtime/cortex/artifacts/runtime/state/atlas/legacy-backfill/*.descriptor.json`

That keeps historical sessions queryable without lying about their epoch or mutating the originals.

## Resume Visibility

Status now exposes governed resume transition data from descriptors only:

- `resume_status`
- `resume_request_ref`
- `resume_dispatch_ref`
- `resume_run_manifest_ref`
- `resumed_assignment_ref`
- `resumed_running_status_ref`
- `resumed_completed_status_ref`
- `resume_context_ref`
- `resume_merge_completion_ref`
- `resume_requested_at`
- `resume_dispatched_at`
- `resume_completed_at`
- `resume_failure_reason`

That makes the transition from `resume_ready` to `running` to `completed` or `resume_failed` visible without reading `_stack` logs directly.

## World-Model Refs

The status payload also reports root-owned world-model artifact refs when present:

- `runtime/state/atlas/world-model.snapshot.latest.json`
- `runtime/state/atlas/world-model.attention.latest.json`

Those artifacts are the global snapshot layer above descriptors and receipts. Status remains descriptor-backed, but it may report the current snapshot and attention digests for clients that need one stable read surface.

## Initiative Surface

Status now exposes initiative-aware slices from structured working memory.

Current output includes:

- `initiatives.active_items`
- `initiatives.open_attention_items`
- `initiatives.proposed_session_items`
- `initiatives.repo_linked_items`

The Mazer D2 learning scorer initiative is the first real repo-linked example: it should surface as active, open-attention, and repo-linked before any proposal executes.

## Conversation Surface

Status now exposes root conversation state from conversation descriptors only.

Current output includes:

- `conversations.item_count`
- `conversations.active_count`
- `conversations.recent_items`

Conversation attention is derived from conversation turn descriptors with `action_mode=proposal_required`.

That keeps proposed follow-up visible in the same governed attention queue as other operator work.

## Open Merge Rule

A merge request remains open until a registered `atlas.stack.supervisor-consumer.v1` descriptor closes the same `merge_request_id`.

## Residue Classification Rule

Status exposes one canonical active merge-request artifact per conflict key or session scope.

Extra merge-request artifacts with the same live conflict surface remain visible as residue instead of competing as equal current truth.

Current status output exposes this through:

- `open_merge_requests`
- `merge_request_residue`

Residue is retention-friendly. It is not deleted automatically, but it is not allowed to confuse current-state reads.

## Governed Write View

Status now exposes the first bounded truthful write class separately from generic execution receipts.

Current output includes:

- `governed_writes`
- `execution_receipt_residue`

`governed_writes` shows only canonical current `workspace_file_apply` receipts. Retained residue stays visible, but it does not compete as current truth.

## Trust Surface Rule

Knowledge status output is metadata-only for quarantined surfaces. The status view must never hydrate raw Verta evidence or derived promotion text for those surfaces.
